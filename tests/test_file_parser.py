import os
import pytest
from app.engine.file_parser import parse_file, ParseResult

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestParseTextFile:
    def test_parse_txt(self):
        result = parse_file(os.path.join(FIXTURES, "sample.txt"))
        assert result.text != ""
        assert "Hello world" in result.text
        assert result.error is None

    def test_parse_csv(self):
        result = parse_file(os.path.join(FIXTURES, "sample.csv"))
        assert "张三" in result.text
        assert result.error is None

    def test_parse_md(self):
        result = parse_file(os.path.join(FIXTURES, "sample.txt"))
        assert result.error is None


class TestParseUnsupported:
    def test_old_doc_returns_error(self):
        result = parse_file("/fake/path/file.doc")
        assert result.text == ""
        assert result.error is not None
        assert "老旧格式" in result.error

    def test_unknown_ext_returns_error(self):
        result = parse_file("/fake/path/file.xyz")
        assert result.text == ""
        assert result.error is not None


class TestParseResult:
    def test_result_dataclass(self):
        r = ParseResult(text="abc", encoding="utf-8", page_count=3)
        assert r.text == "abc"
        assert r.page_count == 3
