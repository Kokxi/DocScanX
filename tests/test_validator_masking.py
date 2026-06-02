import pytest
from app.engine.uie_engine import Entity
from app.engine.validator import (
    validate_entity, validate_entities, filter_valid_entities,
    ValidationResult,
)
from app.engine.masking import mask_entity, mask_text, generate_masked_report


class TestValidator:
    def test_valid_phone(self):
        e = Entity(type="phone", value="13800138000", start=0, end=11)
        vr = validate_entity(e)
        assert vr.is_valid

    def test_invalid_phone_second_digit(self):
        e = Entity(type="phone", value="12000138000", start=0, end=11)
        vr = validate_entity(e)
        assert not vr.is_valid

    def test_valid_email(self):
        e = Entity(type="email", value="user@example.com", start=0, end=16)
        vr = validate_entity(e)
        assert vr.is_valid

    def test_invalid_email(self):
        e = Entity(type="email", value="not-an-email", start=0, end=11)
        vr = validate_entity(e)
        assert not vr.is_valid

    def test_valid_bank_card_luhn(self):
        e = Entity(type="bank_card", value="6222025484816554", start=0, end=16)
        vr = validate_entity(e)
        assert vr.is_valid

    def test_invalid_bank_card_too_short(self):
        e = Entity(type="bank_card", value="123456789012345", start=0, end=15)
        vr = validate_entity(e)
        assert not vr.is_valid

    def test_valid_plate(self):
        e = Entity(type="plate_no", value="京A12345", start=0, end=7)
        vr = validate_entity(e)
        assert vr.is_valid

    def test_invalid_plate(self):
        e = Entity(type="plate_no", value="XX12345", start=0, end=7)
        vr = validate_entity(e)
        assert not vr.is_valid

    def test_validate_entities_batch(self):
        entities = [
            Entity(type="phone", value="13800138000", start=0, end=11),
            Entity(type="email", value="bad-email", start=12, end=21),
        ]
        results = validate_entities(entities)
        assert len(results) == 2
        assert results[0].is_valid
        assert not results[1].is_valid

    def test_filter_valid(self):
        entities = [
            Entity(type="phone", value="13800138000", start=0, end=11),
            Entity(type="phone", value="12000000000", start=12, end=23),
        ]
        valid = filter_valid_entities(entities)
        assert len(valid) == 1


class TestMasking:
    def test_mask_phone(self):
        e = Entity(type="phone", value="13800138000", start=3, end=14)
        text = "电话13800138000联系"
        result = mask_entity(text, e)
        assert "138****8000" in result
        assert "13800138000" not in result

    def test_mask_name_two_chars(self):
        e = Entity(type="name", value="张三", start=3, end=5)
        result = mask_entity("姓名张三测试", e)
        assert "张*" in result
        assert "张三" not in result

    def test_mask_name_three_chars(self):
        e = Entity(type="name", value="王小明", start=0, end=3)
        result = mask_entity("王小明", e)
        assert result == "王*明"

    def test_mask_id_card(self):
        e = Entity(type="id_card", value="110101199001010007", start=0, end=18)
        result = mask_entity("110101199001010007", e)
        assert "110101********0007" in result

    def test_mask_text_multiple(self):
        entities = [
            Entity(type="phone", value="13800138000", start=3, end=14),
            Entity(type="email", value="a@b.com", start=17, end=25),
        ]
        text = "电话13800138000，邮箱a@b.com"
        result = mask_text(text, entities)
        assert "13800138000" not in result
        assert "a@b.com" not in result

    def test_mask_gender(self):
        e = Entity(type="gender", value="女", start=3, end=4)
        result = mask_entity("性别女测试", e)
        assert "*" in result

    def test_generate_masked_report(self):
        entities = [
            Entity(type="phone", value="13800138000", start=0, end=11),
        ]
        report = generate_masked_report("13800138000", entities)
        assert "original" in report
        assert "masked" in report
        assert "mappings" in report
        assert len(report["mappings"]) == 1
        assert report["mappings"][0]["original"] == "13800138000"
