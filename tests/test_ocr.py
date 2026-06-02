import os
import tempfile
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.core.config import init_config
from app.engine.ocr import ocr_image, ocr_pdf_page, OcrResult, OcrBlock


@pytest.fixture(scope="session", autouse=True)
def _init_config():
    """初始化配置（OCR 引擎需要 config 来解析模型路径）。"""
    init_config()


@pytest.fixture
def test_image():
    """创建带文字的测试图片。"""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img = Image.new("RGB", (400, 100), "white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 30), "Test OCR Engine", fill="black")
    img.save(tmp.name)
    tmp.close()  # Windows: 关闭文件句柄避免 PermissionError
    yield tmp.name
    try:
        os.unlink(tmp.name)
    except PermissionError:
        pass


class TestOcrImage:
    def test_basic_ocr(self, test_image):
        result = ocr_image(test_image)
        assert isinstance(result, OcrResult)
        assert result.error is None
        assert result.page_count == 1
        assert result.elapsed > 0

    def test_returns_blocks(self, test_image):
        result = ocr_image(test_image)
        assert len(result.blocks) > 0
        for b in result.blocks:
            assert isinstance(b, OcrBlock)
            assert len(b.text) > 0
            assert 0 <= b.confidence <= 1
            assert len(b.bbox) == 4

    def test_file_not_found(self):
        result = ocr_image("/nonexistent/file.png")
        assert result.error is not None
        assert "不存在" in result.error

    def test_min_confidence_filter(self, test_image):
        result_all = ocr_image(test_image, min_confidence=0.0)
        result_high = ocr_image(test_image, min_confidence=0.99)
        assert len(result_all.blocks) >= len(result_high.blocks)


class TestOcrPdf:
    def test_file_not_found(self):
        result = ocr_pdf_page("/nonexistent/file.pdf", 0)
        assert result.error is not None
