import os
import tempfile
import pytest
from app.engine.pdf_judge import judge_pdf, PdfVerdict


class TestPdfJudge:
    def test_file_not_found(self):
        result = judge_pdf("/nonexistent/file.pdf")
        assert not result.is_text_pdf
        assert result.error != ""

    def test_pdf_verdict_dataclass(self):
        v = PdfVerdict(is_text_pdf=True, needs_ocr=False, total_chars=100, page_count=3)
        assert v.is_text_pdf
        assert not v.needs_ocr
        assert v.total_chars == 100
        assert v.page_count == 3

    def test_non_pdf_returns_error(self):
        """非 PDF 文件被 pdfplumber 打开会抛异常，应被捕获。"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("not a pdf")
            tmp_path = f.name
        try:
            result = judge_pdf(tmp_path)
            assert result.error != ""
        finally:
            os.unlink(tmp_path)
