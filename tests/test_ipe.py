import pytest
from app.engine.uie_engine import Entity
from app.engine.ipe import (
    parse_identities, IpeResult, Person,
    _cluster_entities, _cluster_to_person, _merge_persons,
)


class TestClusterEntities:
    def test_empty(self):
        assert _cluster_entities([], 300) == []

    def test_single_entity(self):
        e = Entity(type="name", value="张三", start=0, end=2)
        clusters = _cluster_entities([e], 300)
        assert len(clusters) == 1
        assert len(clusters[0]) == 1

    def test_nearby_entities_same_cluster(self):
        entities = [
            Entity(type="name", value="张三", start=0, end=2),
            Entity(type="phone", value="13800138000", start=5, end=16),
            Entity(type="email", value="z@b.com", start=20, end=27),
        ]
        clusters = _cluster_entities(entities, 300)
        assert len(clusters) == 1
        assert len(clusters[0]) == 3

    def test_distant_entities_split(self):
        entities = [
            Entity(type="name", value="张三", start=0, end=2),
            Entity(type="phone", value="13800138000", start=500, end=511),
        ]
        clusters = _cluster_entities(entities, 300)
        assert len(clusters) == 2


class TestClusterToPerson:
    def test_with_name(self):
        cluster = [
            Entity(type="name", value="张三", start=0, end=2),
            Entity(type="phone", value="13800138000", start=5, end=16),
        ]
        person = _cluster_to_person(cluster, "")
        assert person is not None
        assert person.name == "张三"
        assert len(person.entities) == 2

    def test_without_name_returns_none(self):
        cluster = [
            Entity(type="phone", value="13800138000", start=5, end=16),
            Entity(type="email", value="a@b.com", start=20, end=27),
        ]
        person = _cluster_to_person(cluster, "")
        assert person is None


class TestMergePersons:
    def test_merge_same_name(self):
        p1 = Person(name="张三", entities=[
            Entity(type="name", value="张三", start=0, end=2),
            Entity(type="phone", value="13800138000", start=5, end=16),
        ])
        p2 = Person(name="张三", entities=[
            Entity(type="name", value="张三", start=0, end=2),
            Entity(type="email", value="a@b.com", start=20, end=27),
        ])
        merged = _merge_persons([p1, p2])
        assert len(merged) == 1
        assert len(merged[0].entities) == 3

    def test_no_merge_different_name(self):
        p1 = Person(name="张三", entities=[])
        p2 = Person(name="李四", entities=[])
        merged = _merge_persons([p1, p2])
        assert len(merged) == 2


class TestParseIdentities:
    def test_empty(self):
        result = parse_identities([])
        assert isinstance(result, IpeResult)
        assert result.persons == []
        assert result.orphans == []

    def test_single_person(self):
        entities = [
            Entity(type="name", value="王五", start=3, end=5),
            Entity(type="phone", value="13800138000", start=8, end=19),
            Entity(type="gender", value="男", start=20, end=21),
        ]
        result = parse_identities(entities)
        assert len(result.persons) == 1
        assert result.persons[0].name == "王五"
        assert result.persons[0].get("phone").value == "13800138000"

    def test_orphans_without_name(self):
        entities = [
            Entity(type="phone", value="13800138000", start=0, end=11),
            Entity(type="email", value="a@b.com", start=15, end=22),
        ]
        result = parse_identities(entities)
        assert len(result.persons) == 0
        assert len(result.orphans) == 2

    def test_two_persons(self):
        entities = [
            Entity(type="name", value="张三", start=0, end=2),
            Entity(type="phone", value="13800138000", start=5, end=16),
            Entity(type="name", value="李四", start=200, end=202),
            Entity(type="phone", value="13900139000", start=205, end=216),
        ]
        result = parse_identities(entities)
        assert len(result.persons) == 2

    def test_to_dict(self):
        entities = [
            Entity(type="name", value="王五", start=0, end=2),
            Entity(type="phone", value="13800138000", start=5, end=16),
        ]
        result = parse_identities(entities)
        d = result.persons[0].to_dict()
        assert d["name"] == "王五"
        assert d["phone"] == "13800138000"
