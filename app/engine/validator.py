"""实体校验器。

对 UIE 提取的实体进行格式校验（身份证/手机号/邮箱/银行卡/车牌等）。
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.engine.uie_engine import Entity


@dataclass
class ValidationResult:
    entity_type: str
    value: str
    is_valid: bool
    reason: str = ""


# ── 校验函数 ────────────────────────────────────────────────

def _validate_id_card(value: str) -> tuple:
    """校验身份证号。返回 (is_valid, reason)。"""
    if len(value) != 18:
        return False, "长度不为18位"
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_map = "10X98765432"
    try:
        total = sum(int(value[i]) * weights[i] for i in range(17))
        expected = check_map[total % 11]
        if value[17].upper() != expected:
            return False, f"校验码不匹配(期望{expected},实际{value[17]})"
        return True, "ok"
    except (ValueError, IndexError):
        return False, "包含非数字字符"


def _validate_phone(value: str) -> tuple:
    """校验手机号。"""
    if len(value) != 11:
        return False, "长度不为11位"
    if not value.startswith("1"):
        return False, "不是1开头"
    if value[1] not in "3456789":
        return False, f"第二位{value[1]}不在有效范围"
    return True, "ok"


def _validate_email(value: str) -> tuple:
    """校验邮箱格式。"""
    pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    if pattern.match(value):
        return True, "ok"
    return False, "邮箱格式不符"


def _validate_bank_card(value: str) -> tuple:
    """校验银行卡号（Luhn 算法）。"""
    digits = value.replace(" ", "")
    if not digits.isdigit():
        return False, "包含非数字字符"
    if len(digits) < 16 or len(digits) > 19:
        return False, f"长度{len(digits)}不在16-19"
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    if total % 10 != 0:
        return False, "Luhn校验失败"
    return True, "ok"


def _validate_plate_no(value: str) -> tuple:
    """校验中国车牌号。"""
    pattern = re.compile(
        r"^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁]"
        r"[A-HJ-NP-Z][A-HJ-NP-Z0-9]{4,5}[A-HJ-NP-Z0-9挂学警港澳]$"
    )
    if pattern.match(value):
        return True, "ok"
    return False, "车牌格式不符"


_VALIDATORS = {
    "id_card": _validate_id_card,
    "phone": _validate_phone,
    "email": _validate_email,
    "bank_card": _validate_bank_card,
    "plate_no": _validate_plate_no,
}


def validate_entity(entity: Entity) -> ValidationResult:
    """校验单个实体。

    Returns:
        ValidationResult: is_valid + reason
    """
    validator = _VALIDATORS.get(entity.type)
    if validator is None:
        return ValidationResult(entity.type, entity.value, True, "无需校验")
    is_valid, reason = validator(entity.value)
    return ValidationResult(entity.type, entity.value, is_valid, reason)


def validate_entities(entities: List[Entity]) -> List[ValidationResult]:
    """批量校验实体列表。"""
    return [validate_entity(e) for e in entities]


def filter_valid_entities(entities: List[Entity]) -> List[Entity]:
    """过滤只保留有效的实体。"""
    results = validate_entities(entities)
    return [e for e, r in zip(entities, results) if r.is_valid]
