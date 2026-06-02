"""信息抽取引擎。

从文本中提取结构化实体（姓名/身份证/手机号/银行卡/地址等）。

当前实现使用正则+启发式规则（Python 3.13 兼容），架构预留 UIE 深度学习模型接口。
当 PaddlePaddle/PaddleNLP 支持 Python 3.13 后可直接切换为 UIE 模型推理。
"""
import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger("system")

# ── 正则规则库（内置默认）──────────────────────────────────────
_PATTERNS: dict = {
    "id_card": re.compile(
        r"(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)"
    ),
    "phone": re.compile(
        r"(?<!\d)1[3-9]\d{9}(?!\d)"
    ),
    "email": re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    ),
    "bank_card": re.compile(
        r"(?<!\d)(?!\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx])\d{16,19}(?!\d)"
    ),
    "plate_no": re.compile(
        r"[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁][A-HJ-NP-Z][A-HJ-NP-Z0-9]{4,5}[A-HJ-NP-Z0-9挂学警港澳]"
    ),
    "passport": re.compile(
        r"[EGK]\d{8}"
    ),
    "wechat": re.compile(
        r"微信[号:：]?\s*([a-zA-Z][a-zA-Z0-9_-]{5,19})"
    ),
    "birthday": re.compile(
        r"(?:19|20)\d{2}[-/年](?:0[1-9]|1[0-2])[-/月](?:0[1-9]|[12]\d|3[01])[日号]?"
    ),
    "job_no": re.compile(
        r"(?:工号|员工号|Job\s*No\.?)[:：\s]*([A-Z0-9]{4,20})",
        re.IGNORECASE,
    ),
    "gender": re.compile(
        r"[男女](?:士|性)?"
    ),
    "name": re.compile(
        r"(?:姓名|名字|持卡人|开户人|联系人|负责人|法人|申请人)[:：\s]*([一-鿿]{2,4})(?:先生|女士|同志)?"
    ),
    "address": re.compile(
        r"(?:地址|住址|所在地|位于)[:：\s]*"
        r"([一-鿿]{2,}(?:省|自治区|市|区|县|镇|乡|村|路|街|巷|号|楼|层|室|单元|栋|幢))"
        r"[一-鿿0-9\-,，\s]{4,50}"
    ),
}

# 标记哪些是标准格式（不建议用户修改）
_STANDARD_TYPES: set = {"id_card", "phone", "email", "bank_card"}

_custom_patterns_cache = None


def _get_patterns() -> dict:
    """获取当前生效的正则规则（合并 config 自定义 + 内置默认）。"""
    global _custom_patterns_cache
    try:
        from app.core.config import config as app_config
        if app_config and hasattr(app_config, "extraction"):
            ext = app_config.extraction
            custom = getattr(ext, "patterns", None)
            if custom and isinstance(custom, dict):
                # 检查自定义规则是否与上次缓存一致
                cache_key = tuple(sorted(custom.items()))
                if _custom_patterns_cache and _custom_patterns_cache[0] == cache_key:
                    return _custom_patterns_cache[1]
                # 合并：自定义优先，其余用默认
                merged = dict(_PATTERNS)
                flags = {"job_no": re.IGNORECASE}
                for k, v in custom.items():
                    if k in _PATTERNS and isinstance(v, str) and v.strip():
                        try:
                            merged[k] = re.compile(v, flags.get(k, 0))
                        except re.error:
                            logger.warning(f"自定义正则无效 [{k}]: {v}")
                _custom_patterns_cache = (cache_key, merged)
                return merged
    except Exception:
        pass
    return _PATTERNS


def get_pattern_strings() -> dict:
    """返回当前生效的正则字符串（供前端展示）。"""
    patterns = _get_patterns()
    return {k: v.pattern for k, v in patterns.items()}


def get_default_pattern_strings() -> dict:
    """返回内置默认正则字符串（供前端恢复默认）。"""
    return {k: v.pattern for k, v in _PATTERNS.items()}


def is_standard_type(entity_type: str) -> bool:
    """判断是否为标准格式类型。"""
    return entity_type in _STANDARD_TYPES

# 银行卡 BIN 码（前6位）校验表 — 主流银行
_BANK_BINS: dict = {
    "622202": "工商银行", "622203": "工商银行", "621226": "工商银行",
    "622848": "农业银行", "622846": "农业银行",
    "621700": "建设银行", "622700": "建设银行",
    "621661": "中国银行", "621663": "中国银行",
    "622260": "交通银行",
    "621691": "招商银行", "622588": "招商银行",
    "622908": "兴业银行", "622909": "兴业银行",
    "622521": "浦发银行", "622522": "浦发银行",
    "622619": "光大银行", "622616": "光大银行",
    "622155": "民生银行", "622156": "民生银行",
    "622688": "中信银行", "622689": "中信银行",
    "622155": "平安银行",
}


@dataclass
class Entity:
    type: str
    value: str
    start: int
    end: int
    confidence: float = 1.0


@dataclass
class ExtractionResult:
    text: str = ""
    entities: List[Entity] = field(default_factory=list)
    error: Optional[str] = None


def _validate_id_card(card_no: str) -> bool:
    """校验身份证号校验码。"""
    if len(card_no) != 18:
        return False
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_map = "10X98765432"
    try:
        total = sum(int(card_no[i]) * weights[i] for i in range(17))
        return check_map[total % 11] == card_no[17].upper()
    except (ValueError, IndexError):
        return False


def _extract_regex(text: str, entity_type: str, pattern) -> List[Entity]:
    """用正则从文本提取实体。"""
    entities = []
    for m in pattern.finditer(text):
        if m.groups():
            val = m.group(1) or m.group(0)
            start = m.start(1) if m.lastindex else m.start()
        else:
            val = m.group(0)
            start = m.start()
        end = start + len(val)
        entities.append(Entity(type=entity_type, value=val, start=start, end=end))
    return entities


def _deduplicate(entities: List[Entity]) -> List[Entity]:
    """按位置去重，重叠的取置信度高的。"""
    if not entities:
        return entities
    entities.sort(key=lambda e: (e.start, -e.confidence))
    result = [entities[0]]
    for e in entities[1:]:
        last = result[-1]
        if e.start < last.end and e.end > last.start:
            if e.confidence > last.confidence:
                result[-1] = e
        else:
            result.append(e)
    return result


# 明确的非姓名词汇，避免误识别
_NON_NAME_WORDS = {
    "身份证", "银行卡", "手机号", "邮箱号", "微信号", "地址码",
    "工本费", "手续费", "管理费", "保证金", "违约金", "赔偿金",
    "工作日", "休息日", "节假日", "签字笔", "笔记本",
    "申请人", "持卡人", "联系人", "负责人", "开户人", "经办人", "所有人",
    "北京市", "上海市", "天津市", "重庆市",
}

# 中国常见姓氏（百家姓前100）
_COMMON_SURNAMES = {
    "赵", "钱", "孙", "李", "周", "吴", "郑", "王", "冯", "陈", "褚", "卫", "蒋", "沈", "韩", "杨",
    "朱", "秦", "尤", "许", "何", "吕", "施", "张", "孔", "曹", "严", "华", "金", "魏", "陶", "姜",
    "戚", "谢", "邹", "喻", "柏", "水", "窦", "章", "云", "苏", "潘", "葛", "奚", "范", "彭", "郎",
    "鲁", "韦", "昌", "马", "苗", "凤", "花", "方", "俞", "任", "袁", "柳", "酆", "鲍", "史", "唐",
    "费", "廉", "岑", "薛", "雷", "贺", "倪", "汤", "滕", "殷", "罗", "毕", "郝", "邬", "安", "常",
    "乐", "于", "时", "傅", "皮", "卞", "齐", "康", "伍", "余", "元", "卜", "顾", "孟", "平", "黄",
    "和", "穆", "萧", "尹", "姚", "邵", "湛", "汪", "祁", "毛", "禹", "狄", "米", "贝", "明", "臧",
    "计", "伏", "成", "戴", "谈", "宋", "茅", "庞", "熊", "纪", "舒", "屈", "项", "祝", "董", "梁",
    "杜", "阮", "蓝", "闵", "席", "季", "麻", "强", "贾", "路", "娄", "危", "江", "童", "颜", "郭",
    "梅", "盛", "林", "刁", "钟", "徐", "邱", "骆", "高", "夏", "蔡", "田", "樊", "胡", "凌", "霍",
    "虞", "万", "支", "柯", "咎", "管", "卢", "莫", "经", "房", "裘", "缪", "干", "解", "应", "宗",
    "丁", "宣", "贲", "邓", "郁", "单", "杭", "洪", "包", "诸", "左", "石", "崔", "吉", "钮", "龚",
    "程", "嵇", "邢", "滑", "裴", "陆", "荣", "翁", "荀", "羊", "於", "惠", "甄", "曲", "家", "封",
    "芮", "羿", "储", "靳", "汲", "邴", "糜", "松", "井", "段", "富", "巫", "乌", "焦", "巴", "弓",
    "牧", "隗", "山", "谷", "车", "侯", "宓", "蓬", "全", "郗", "班", "仰", "秋", "仲", "伊", "宫",
    "宁", "仇", "栾", "暴", "甘", "钭", "厉", "戎", "祖", "武", "符", "刘", "景", "詹", "束", "龙",
    "叶", "幸", "司", "韶", "郜", "黎", "蓟", "薄", "印", "宿", "白", "怀", "蒲", "邰", "从", "鄂",
    "索", "咸", "籍", "赖", "卓", "蔺", "屠", "蒙", "池", "乔", "阴", "郁", "胥", "能", "苍", "双",
    "闻", "莘", "党", "翟", "谭", "贡", "劳", "逄", "姬", "申", "扶", "堵", "冉", "宰", "郦", "雍",
    "却", "璩", "桑", "桂", "濮", "牛", "寿", "通", "边", "扈", "燕", "冀", "郏", "浦", "尚", "农",
    "温", "别", "庄", "晏", "柴", "瞿", "阎", "充", "慕", "连", "茹", "习", "宦", "艾", "鱼", "容",
    "向", "古", "易", "慎", "戈", "廖", "庚", "终", "暨", "居", "衡", "步", "都", "耿", "满", "弘",
    "匡", "国", "文", "寇", "广", "禄", "阙", "东", "殴", "殳", "沃", "利", "蔚", "越", "夔", "隆",
    "师", "巩", "厍", "聂", "晁", "勾", "敖", "融", "冷", "訾", "辛", "阚", "那", "简", "饶", "空",
    "曾", "毋", "沙", "乜", "养", "鞠", "须", "丰", "巢", "关", "蒯", "相", "查", "后", "荆", "红",
    "游", "竺", "权", "逯", "盖", "益", "桓", "公",
}


def _extract_standalone_names(text: str, existing_entities: List[Entity]) -> List[Entity]:
    """从未被实体覆盖的区域提取独立中文姓名。"""
    # 找出已被匹配的字符位置
    covered = set()
    for e in existing_entities:
        for i in range(e.start, e.end):
            covered.add(i)

    entities = []
    # 匹配独立出现的2-4个连续中文字符
    pattern = re.compile(r"(?:^|[\s\n,，。、;；:：/\-—])[一-鿿]{2,4}(?=[\s\n,，。、;；:：/\-—]|$)")
    for m in pattern.finditer(text):
        raw = m.group(0)
        val = re.sub(r'^[\s,，。、;；:：/\-—]+', '', raw)

        # 过滤非姓名词汇
        if val in _NON_NAME_WORDS:
            continue
        # 必须包含常见姓氏才判定为姓名
        if val[0] not in _COMMON_SURNAMES:
            continue
        # 检查是否与已有实体重叠
        start = m.start()
        # 跳过前导分隔符
        while start < m.end() and text[start] in r" \n,，。、;；:：/\-—":
            start += 1
        end = start + len(val)
        if any(i in covered for i in range(start, end)):
            continue
        entities.append(Entity(type="name", value=val, start=start, end=end, confidence=0.6))

    return entities


def extract_entities(text: str, schema: Optional[List[str]] = None,
                     min_confidence: float = 0.5) -> ExtractionResult:
    """从文本中提取实体。

    Args:
        text: 输入文本
        schema: 需要提取的实体类型列表，默认全部
        min_confidence: 最低置信度

    Returns:
        ExtractionResult: 提取结果
    """
    if not text or not text.strip():
        return ExtractionResult(text=text)

    patterns = _get_patterns()

    if schema is None:
        schema = list(patterns.keys())

    entities: List[Entity] = []

    for entity_type in schema:
        if entity_type not in patterns:
            continue
        pattern = patterns[entity_type]
        found = _extract_regex(text, entity_type, pattern)

        # 特殊校验：身份证
        if entity_type == "id_card":
            found = [e for e in found if _validate_id_card(e.value)]
            for e in found:
                e.confidence = 0.95

        # 银行卡去除非法的
        if entity_type == "bank_card":
            found = [e for e in found if e.value[:6] in _BANK_BINS or 16 <= len(e.value) <= 19]
            for e in found:
                e.confidence = 0.85 if e.value[:6] in _BANK_BINS else 0.5

        # 过滤低置信度
        found = [e for e in found if e.confidence >= min_confidence]
        entities.extend(found)

    # 无标签前缀的独立姓名检测（行首或逗号/句号后的中文人名）
    if "name" in schema:
        standalone_names = _extract_standalone_names(text, entities)
        entities.extend(standalone_names)

    entities = _deduplicate(entities)
    entities.sort(key=lambda e: e.start)

    return ExtractionResult(text=text, entities=entities)
