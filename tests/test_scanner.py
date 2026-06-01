import os
import zipfile
import tempfile
import pytest
from app.engine.scanner import scan_directory, FileInfo


@pytest.fixture
def test_dir():
    """创建测试目录结构。"""
    tmp = tempfile.mkdtemp()
    # 文本文件
    with open(os.path.join(tmp, "readme.txt"), "w") as f:
        f.write("hello")
    with open(os.path.join(tmp, "data.csv"), "w") as f:
        f.write("a,b,c")
    # 不支持的文件（image 分组，默认关闭）
    with open(os.path.join(tmp, "image.bmp"), "w") as f:
        f.write("fake")
    # 子目录
    sub = os.path.join(tmp, "subdir")
    os.makedirs(sub)
    with open(os.path.join(sub, "notes.md"), "w") as f:
        f.write("notes")
    # zip
    zip_path = os.path.join(tmp, "bundle.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("inside.txt", "inside")
    yield tmp
    import shutil
    shutil.rmtree(tmp)


class TestScanDirectory:
    def test_flat_directory(self, test_dir):
        results = scan_directory(test_dir, include_subdir=False)
        exts = {r.ext for r in results}
        assert ".txt" in exts
        assert ".csv" in exts

    def test_include_subdir(self, test_dir):
        results = scan_directory(test_dir, include_subdir=True)
        paths = [r.path for r in results]
        assert any("subdir" in p for p in paths)

    def test_ext_groups_filter(self, test_dir):
        groups = {"text": True, "archive": False, "office_new": False, "pdf": False}
        results = scan_directory(test_dir, ext_groups=groups)
        all_text = all(r.ext in {".txt", ".csv", ".md", ".log"} for r in results)
        assert all_text

    def test_archive_extraction(self, test_dir):
        groups = {"archive": True, "text": True, "office_new": False, "pdf": False}
        results = scan_directory(test_dir, ext_groups=groups)
        inside = [r for r in results if "inside.txt" in r.path]
        assert len(inside) > 0

    def test_empty_directory(self):
        tmp = tempfile.mkdtemp()
        results = scan_directory(tmp, include_subdir=True)
        assert results == []
        os.rmdir(tmp)

    def test_no_filter_includes_all(self, test_dir):
        """不传 ext_groups 时，所有识别出的文件类型都包含。"""
        results = scan_directory(test_dir, include_subdir=False)
        exts = {r.ext for r in results}
        assert ".txt" in exts
        assert ".csv" in exts
        assert ".bmp" in exts
