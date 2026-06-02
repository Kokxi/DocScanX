import pytest
from app.engine.uie_engine import (
    extract_entities, ExtractionResult, Entity,
    _validate_id_card, _PATTERNS,
)


class TestIdCardValidation:
    def test_valid_id_card(self):
        assert _validate_id_card("110101199001010007") is True

    def test_invalid_checksum(self):
        assert _validate_id_card("110101199003077654") is False

    def test_wrong_length(self):
        assert _validate_id_card("12345678901234567") is False  # 17位
        assert _validate_id_card("1234567890123456789") is False  # 19位


class TestRegexPatterns:
    def test_phone_pattern(self):
        pattern = _PATTERNS["phone"]
        assert pattern.search("手机13800138000测试")
        assert not pattern.search("电话号码是00000000000")
        assert not pattern.search("金额12000000000元")  # 不以1开头

    def test_email_pattern(self):
        pattern = _PATTERNS["email"]
        assert pattern.search("邮箱test@example.com")
        assert pattern.search("联系a.b+c@mail.co.uk")

    def test_plate_pattern(self):
        pattern = _PATTERNS["plate_no"]
        m = pattern.search("车牌京A12345")
        assert m is not None
        assert m.group() == "京A12345"

    def test_birthday_pattern(self):
        pattern = _PATTERNS["birthday"]
        assert pattern.search("出生1990年05月20日")


class TestExtractEntities:
    def test_empty_text(self):
        result = extract_entities("")
        assert isinstance(result, ExtractionResult)
        assert result.entities == []

    def test_extract_phone_and_email(self):
        text = "电话13800138000，邮箱user@test.com"
        result = extract_entities(text)
        types = {e.type for e in result.entities}
        assert "phone" in types
        assert "email" in types

    def test_extract_with_name_prefix(self):
        text = "姓名：张三，性别：男"
        result = extract_entities(text)
        names = [e for e in result.entities if e.type == "name"]
        assert any("张三" in e.value for e in names)

    def test_deduplicate_overlapping(self):
        """重叠的实体去重保留高置信度。"""
        text = "银行卡6222021234567890"
        result = extract_entities(text)
        # 不应有两个实体覆盖同一段文本
        bank_cards = [e for e in result.entities if e.type == "bank_card"]
        assert len(bank_cards) == 1

    def test_custom_schema(self):
        text = "电话13800138000，邮箱user@test.com"
        result = extract_entities(text, schema=["phone"])
        types = {e.type for e in result.entities}
        assert types == {"phone"}
