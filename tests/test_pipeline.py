import os
import tempfile
import pytest
from PIL import Image, ImageDraw

from app.core.config import init_config
from app.engine.pipeline import process_file, process_directory, FileProcessResult, PipelineResult


@pytest.fixture(scope="session", autouse=True)
def _init_config():
    init_config()


class TestProcessFile:
    def test_txt_with_entities(self):
        """处理包含个人信息的文本文件。"""
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False, encoding="utf-8")
        tmp.write("姓名：张三，电话13800138000，邮箱zhang@test.com")
        tmp.close()
        try:
            result = process_file(tmp.name, ext=".txt")
            assert isinstance(result, FileProcessResult)
            assert result.parse_result is not None
            assert result.ipe_result is not None
            assert len(result.ipe_result.persons) == 1
            assert result.ipe_result.persons[0].name == "张三"
        finally:
            os.unlink(tmp.name)

    def test_empty_txt(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False, encoding="utf-8")
        tmp.write("这是一段没有个人信息的话。")
        tmp.close()
        try:
            result = process_file(tmp.name, ext=".txt")
            assert result.parse_result is not None
            assert result.error is None or "未能提取" in (result.error or "")
        finally:
            os.unlink(tmp.name)

    def test_nonexistent_file(self):
        result = process_file("/nonexistent/path.txt", ext=".txt")
        assert result.error is not None

    def test_csv_with_entities(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False, encoding="utf-8")
        tmp.write("name,phone,email\n张三,13800138000,zhang@test.com\n李四,13900139000,li@test.com")
        tmp.close()
        try:
            result = process_file(tmp.name, ext=".csv")
            assert result.parse_result is not None
            # CSV 数据应该能提取到实体
            assert result.extraction_result is not None
        finally:
            os.unlink(tmp.name)

    def test_returns_masked_report(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False, encoding="utf-8")
        tmp.write("姓名：张三，手机13800138000")
        tmp.close()
        try:
            result = process_file(tmp.name, ext=".txt")
            assert result.masked_report is not None
            assert "masked" in result.masked_report
            assert "mappings" in result.masked_report
            # 确认脱敏后的文本不含明文手机号
            masked_text = result.masked_report["masked"]
            assert "13800138000" not in masked_text
        finally:
            os.unlink(tmp.name)

    def test_image_ocr_and_extract(self):
        """图片 OCR + 信息提取完整流程。"""
        img = Image.new("RGB", (600, 80), "white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 15), "Name: Zhang San Phone: 13800138000", fill="black")
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(tmp.name)
        tmp.close()
        try:
            result = process_file(tmp.name, ext=".png")
            assert result.parse_result is not None or result.ocr_result is not None
        finally:
            try:
                os.unlink(tmp.name)
            except PermissionError:
                pass


class TestProcessDirectory:
    def test_directory_scan_and_process(self):
        tmpdir = tempfile.mkdtemp()
        # 创建测试文件
        with open(os.path.join(tmpdir, "test1.txt"), "w", encoding="utf-8") as f:
            f.write("姓名：张三，电话13800138000")
        with open(os.path.join(tmpdir, "test2.txt"), "w", encoding="utf-8") as f:
            f.write("申请人：李四，身份证号110101199001010007")
        try:
            result = process_directory(tmpdir, include_subdir=False)
            assert isinstance(result, PipelineResult)
            assert len(result.files) == 2
            # 至少有一个文件成功提取到人
            assert result.total_persons >= 1
        finally:
            import shutil
            shutil.rmtree(tmpdir)
