"""敏感信息脱敏。

对提取出的实体在文本中进行遮盖/替换，生成脱敏后的文本。
"""
from typing import List, Optional

from app.engine.uie_engine import Entity


def _mask_by_type(entity_type: str, value: str) -> str:
    """按实体类型返回脱敏后的值。"""
    length = len(value)
    if length == 0:
        return ""

    if entity_type == "name":
        if length <= 2:
            return value[0] + "*"
        return value[0] + "*" * (length - 2) + value[-1]

    if entity_type == "gender":
        return "*"

    if entity_type in ("phone", "id_card"):
        if entity_type == "phone":
            return value[:3] + "****" + value[7:]
        return value[:6] + "********" + value[14:]

    if entity_type == "email":
        at_pos = value.find("@")
        if at_pos > 0:
            local = value[:at_pos]
            domain = value[at_pos:]
            if len(local) <= 3:
                return local[0] + "***" + domain
            return local[:3] + "***" + domain
        return "***@***"

    if entity_type == "bank_card":
        return value[:4] + " **** **** " + value[-4:]

    if entity_type in ("passport", "plate_no"):
        return value[:2] + "***" + value[-2:]

    if entity_type == "birthday":
        return "****-**-**"

    if entity_type == "wechat":
        return value[:3] + "****"

    if entity_type == "address":
        return value[:9] + "****"

    # 默认：保留首尾各1/4
    keep = max(1, length // 4)
    return value[:keep] + "*" * (length - 2 * keep) + value[-keep:]


def mask_entity(text: str, entity: Entity, placeholder: Optional[str] = None) -> str:
    """在文本中遮盖单个实体。

    Args:
        text: 原始文本
        entity: 要遮盖的实体
        placeholder: 自定义占位符，None 则自动生成遮蔽样式

    Returns:
        遮盖后的文本
    """
    if placeholder is None:
        placeholder = _mask_by_type(entity.type, entity.value)
    return text[:entity.start] + placeholder + text[entity.end:]


def mask_text(text: str, entities: List[Entity]) -> str:
    """对文本中所有实体进行脱敏。

    从后往前替换以避免位置偏移问题。

    Returns:
        脱敏后的文本
    """
    result = text
    for entity in sorted(entities, key=lambda e: e.start, reverse=True):
        result = mask_entity(result, entity)
    return result


def generate_masked_report(original: str, entities: List[Entity]) -> dict:
    """生成脱敏对照报告。

    Returns:
        {"original": str, "masked": str, "mappings": [{"type": str, "masked": str}]}
    """
    mappings = []
    for e in entities:
        mappings.append({
            "type": e.type,
            "original": e.value,
            "masked": _mask_by_type(e.type, e.value),
            "confidence": e.confidence,
        })
    return {
        "original": original,
        "masked": mask_text(original, entities),
        "mappings": mappings,
    }
