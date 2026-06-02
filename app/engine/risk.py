"""敏感信息风险评分。

按实体类型加权计分，输出风险等级标签，供数据主体列表和报告使用。
"""
from app.engine.ipe import Person

# 实体类型 → 风险权重
_WEIGHTS: dict = {
    "id_card": 0.30,
    "bank_card": 0.25,
    "passport": 0.25,
    "phone": 0.15,
    "address": 0.10,
    "email": 0.10,
    "wechat": 0.05,
    "birthday": 0.05,
    "plate_no": 0.05,
    "job_no": 0.03,
    "gender": 0.03,
    "name": 0.02,
}

# 评分 → 标签
_THRESHOLDS: list = [
    (0.70, "极高", "critical"),
    (0.45, "高", "high"),
    (0.20, "中", "medium"),
    (0.00, "低", "low"),
]


def score_person(person: Person) -> dict:
    """对单个人计算风险评分，返回附加了 risk 字段的 dict。"""
    score = 0.0
    for e in person.entities:
        score += _WEIGHTS.get(e.type, 0.02)
    score = min(score, 1.0)

    label = "低"
    css = "low"
    for threshold, lbl, cls in _THRESHOLDS:
        if score >= threshold:
            label = lbl
            css = cls
            break

    return {"risk_score": round(score, 2), "risk": label, "risk_level": css}


def add_risk_to_person(person: Person) -> Person:
    """原地修改 Person，附加风险评分字段。"""
    r = score_person(person)
    person.risk_score = r["risk_score"]
    person.risk_label = r["risk"]
    person.risk_level = r["risk_level"]
    return person


def add_risk_to_person_dict(person_dict: dict) -> dict:
    """对 Person.to_dict() 输出的 dict 附加风险字段。"""
    entities = []
    for etype, weight in _WEIGHTS.items():
        if etype in person_dict:
            entities.append((etype, weight))
    # 也检查 name
    score = sum(w for _, w in entities) + (0.02 if "name" in person_dict else 0)
    score = min(score, 1.0)

    label = "低"
    css = "low"
    for threshold, lbl, cls in _THRESHOLDS:
        if score >= threshold:
            label = lbl
            css = cls
            break

    person_dict["risk_score"] = round(score, 2)
    person_dict["risk"] = label
    person_dict["risk_level"] = css
    return person_dict


def risk_distribution(persons: list) -> dict:
    """计算风险等级分布。"""
    dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for p in persons:
        if isinstance(p, dict):
            lvl = p.get("risk_level", "low")
        else:
            lvl = getattr(p, "risk_level", "low")
        dist[lvl] = dist.get(lvl, 0) + 1
    return dist
