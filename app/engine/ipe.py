"""IPE (Identity Parsing Engine) — 身份解析引擎。

将分散的实体按上下文距离聚合为人员记录。
同名+共现实体归并，无主实体挂靠最近人员。
"""
from dataclasses import dataclass, field
from typing import List, Optional

from app.engine.uie_engine import Entity

# 实体离姓名多远（字符数）算作同一人
DEFAULT_PROXIMITY = 300


@dataclass
class Person:
    name: str
    entities: List[Entity] = field(default_factory=list)
    source_text: str = ""
    confidence: float = 1.0

    def get(self, entity_type: str) -> Optional[Entity]:
        for e in self.entities:
            if e.type == entity_type:
                return e
        return None

    def to_dict(self) -> dict:
        result = {"name": self.name, "confidence": self.confidence}
        for e in self.entities:
            result[e.type] = e.value
        return result


@dataclass
class IpeResult:
    persons: List[Person] = field(default_factory=list)
    orphans: List[Entity] = field(default_factory=list)


def _cluster_entities(entities: List[Entity], proximity: int) -> list:
    """将实体按距离聚集为簇，每个簇以最近的 name 为中心。"""
    if not entities:
        return []

    sorted_entities = sorted(entities, key=lambda e: e.start)
    clusters: List[List[Entity]] = []
    current_cluster: List[Entity] = []
    current_name: Optional[Entity] = None
    cluster_start = 0

    for e in sorted_entities:
        if not current_cluster:
            current_cluster = [e]
            cluster_start = e.start
            if e.type == "name":
                current_name = e
            continue

        # 是否在 proximity 范围内
        if e.start - cluster_start <= proximity:
            # 新 name 且距离足够远 → 开启新簇
            if e.type == "name" and current_name and e.start - current_name.start > proximity // 2:
                clusters.append(current_cluster)
                current_cluster = [e]
                cluster_start = e.start
                current_name = e
            else:
                current_cluster.append(e)
                if e.type == "name" and not current_name:
                    current_name = e
        else:
            clusters.append(current_cluster)
            current_cluster = [e]
            cluster_start = e.start
            current_name = e if e.type == "name" else None

    if current_cluster:
        clusters.append(current_cluster)

    return clusters


def _cluster_to_person(cluster: List[Entity], source_text: str) -> Optional[Person]:
    """将一个实体簇转为 Person 记录。无 name 则返回 None。"""
    name_entity = next((e for e in cluster if e.type == "name"), None)
    if name_entity is None:
        return None

    # 取置信度最高的 name
    names = [e for e in cluster if e.type == "name"]
    best_name = max(names, key=lambda e: e.confidence)

    others = [e for e in cluster if e.type != "name"]
    # 同类型去重保留高置信度
    seen = {}
    deduped = []
    for e in others:
        if e.type not in seen or e.confidence > seen[e.type].confidence:
            if e.type in seen:
                deduped.remove(seen[e.type])
            seen[e.type] = e
            deduped.append(e)

    # 计算整体置信度
    confs = [best_name.confidence] + [e.confidence for e in deduped]
    avg_conf = sum(confs) / len(confs) if confs else 1.0

    return Person(
        name=best_name.value,
        entities=[best_name] + deduped,
        source_text=source_text,
        confidence=round(avg_conf, 2),
    )


def _merge_persons(persons: List[Person]) -> List[Person]:
    """合并同名+同证件的重复人员。"""
    merged: List[Person] = []
    for p in persons:
        found = False
        for m in merged:
            # 同名且同身份证/手机号 → 合并
            if m.name == p.name:
                m.entities.extend(p.entities)
                # 重新去重
                seen = {}
                for e in m.entities:
                    if e.type not in seen or e.confidence > seen[e.type].confidence:
                        seen[e.type] = e
                m.entities = list(seen.values())
                m.confidence = min(m.confidence, p.confidence)
                found = True
                break
            # 同身份证号但不同名 → 可能是同一人（更名/别名）
            m_id = m.get("id_card")
            p_id = p.get("id_card")
            if m_id and p_id and m_id.value == p_id.value:
                m.entities.extend(p.entities)
                m.confidence = 0.8  # 降置信度标记
                found = True
                break
        if not found:
            merged.append(p)
    return merged


def parse_identities(entities: List[Entity], source_text: str = "",
                     proximity: int = DEFAULT_PROXIMITY) -> IpeResult:
    """将实体列表解析为人员记录。

    Args:
        entities: 从文本中提取的实体列表
        source_text: 原始文本（用于上下文）
        proximity: 实体归并的距离阈值（字符数）

    Returns:
        IpeResult: persons + orphans
    """
    if not entities:
        return IpeResult()

    clusters = _cluster_entities(entities, proximity)

    persons = []
    orphans = []

    for cluster in clusters:
        person = _cluster_to_person(cluster, source_text)
        if person:
            persons.append(person)
        else:
            # 无 name 的簇 → orphans
            orphans.extend(cluster)

    persons = _merge_persons(persons)

    return IpeResult(persons=persons, orphans=orphans)
