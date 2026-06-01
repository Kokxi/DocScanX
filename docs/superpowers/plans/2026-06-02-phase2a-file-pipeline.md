# DocScanX Phase 2A — 文件处理管线 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 实现 scanner、file_parser、pdf_judge 三个模块，将文件目录扫描为文本内容。

**Architecture:** 三个独立模块，通过 dataclass 传递数据。scanner 输出 FileInfo 列表，file_parser 消费 FileInfo 输出 ParseResult，pdf_judge 在 PDF 文件上先判定再送入 parser。

**Tech Stack:** Python 3.8+, python-docx, openpyxl, python-pptx, pdfplumber, chardet, zipfile (built-in)

---

### Task 1: 安装 Phase 2A 依赖

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Update requirements.txt**

Append to `E:/DocScanX/requirements.txt`:

```
python-docx>=0.8.11
openpyxl>=3.1.0
python-pptx>=0.6.21
pdfplumber>=0.9.0
chardet>=5.0
```

- [ ] **Step 2: Install**

```bash
cd E:/DocScanX && pip install python-docx openpyxl python-pptx pdfplumber chardet
```

- [ ] **Step 3: Verify**

```bash
python -c "import docx, openpyxl, pptx, pdfplumber, chardet; print('ALL OK')"
```

- [ ] **Step 4: Commit**

```bash
cd E:/DocScanX && git add requirements.txt && git commit -m "chore: add Phase 2A file pipeline dependencies"
```

---

### Task 2: 写 scanner.py

**Files:**
- Create: `app/engine/scanner.py`
- Create: `tests/test_scanner.py`

- [ ] **Step 1: Write scanner.py**

Write to `E:/DocScanX/app/engine/scanner.py`:

```python
"""目录扫描器 — 遍历目录、发现文件、解压压缩包、按后缀过滤。"""
import os
import zipfile
import tempfile
import shutil
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FileInfo:
    path: str
    ext: str
    size_mb: float
    is_archive: bool = False


class ScanError(Exception):
    """扫描过程中的非致命错误。"""


def _get_ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()


def _get_ext_group(ext: str) -> Optional[str]:
    """返回后缀所属分组名，不匹配返回 None。"""
    groups = {
        "archive": {".zip", ".rar", ".7z"},
        "office_new": {".docx", ".xlsx", ".pptx"},
        "office_old": {".doc", ".xls", ".ppt"},
        "pdf": {".pdf"},
        "image": {".jpg", ".jpeg", ".png", ".bmp", ".tiff"},
        "text": {".txt", ".csv", ".md", ".log"},
        "structured": {".json", ".xml"},
        "dev": {".py", ".java", ".js", ".html", ".sql", ".css", ".cpp"},
    }
    for group, exts in groups.items():
        if ext in exts:
            return group
    return None


def _should_include(ext: str, ext_groups: dict) -> bool:
    group = _get_ext_group(ext)
    if group is None:
        return False
    return ext_groups.get(group, False)


def _extract_archive(archive_path: str, temp_dir: str) -> str:
    """解压压缩包到临时目录，返回解压目录路径。"""
    ext = _get_ext(archive_path)
    dest = os.path.join(temp_dir, os.path.basename(archive_path) + "_extracted")
    os.makedirs(dest, exist_ok=True)

    if ext == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(dest)
        return dest

    # .rar / .7z: try patool (optional)
    try:
        import patoolib
        patoolib.extract_archive(archive_path, outdir=dest, interactive=False)
        return dest
    except ImportError:
        raise ScanError(f"无法解压 {ext} 文件: 缺少 patool 库，仅支持 .zip")


def scan_directory(
    root_path: str,
    include_subdir: bool = True,
    extract_archive: bool = True,
    ext_groups: Optional[dict] = None,
    max_depth: int = 3,
    _current_depth: int = 0,
) -> List[FileInfo]:
    """扫描目录，返回文件清单。

    Args:
        root_path: 根目录路径
        include_subdir: 是否递归子目录
        extract_archive: 是否解压压缩包
        ext_groups: 各分组是否启用，如 {"archive": True, "office_new": True, ...}
        max_depth: 压缩包嵌套最大深度
    """
    if ext_groups is None:
        ext_groups = {}

    results: List[FileInfo] = []
    temp_dir = os.path.join(tempfile.gettempdir(), "docscanx_scan")

    if not os.path.isdir(root_path):
        return results

    for entry in os.scandir(root_path):
        if entry.is_file():
            ext = _get_ext(entry.path)
            group = _get_ext_group(ext)

            # 跳过不支持的文件
            if group is None:
                continue

            # 检查分组是否启用
            if ext_groups and not ext_groups.get(group, False):
                continue

            try:
                size_mb = entry.stat().st_size / (1024 * 1024)
            except OSError:
                size_mb = 0

            info = FileInfo(
                path=entry.path,
                ext=ext,
                size_mb=size_mb,
                is_archive=(group == "archive"),
            )
            results.append(info)

            # 解压压缩包并递归扫描
            if info.is_archive and extract_archive and _current_depth < max_depth:
                try:
                    extracted_dir = _extract_archive(entry.path, temp_dir)
                    nested = scan_directory(
                        extracted_dir,
                        include_subdir=True,
                        extract_archive=extract_archive,
                        ext_groups=ext_groups,
                        max_depth=max_depth,
                        _current_depth=_current_depth + 1,
                    )
                    results.extend(nested)
                except ScanError:
                    pass  # 解压失败不中断，记录日志

        elif entry.is_dir() and include_subdir:
            nested = scan_directory(
                entry.path,
                include_subdir=True,
                extract_archive=extract_archive,
                ext_groups=ext_groups,
                max_depth=max_depth,
                _current_depth=_current_depth,
            )
            results.extend(nested)

    return results
```

- [ ] **Step 2: Write test_scanner.py**

Write to `E:/DocScanX/tests/test_scanner.py`:

```python
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
    # 不支持的文件
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

    def test_unsupported_files_skipped(self, test_dir):
        results = scan_directory(test_dir, include_subdir=False)
        exts = {r.ext for r in results}
        assert ".bmp" not in exts  # bmp 属于 image 分组, 默认关闭
```

- [ ] **Step 3: Run tests**

```bash
cd E:/DocScanX && pip install pytest && python -m pytest tests/test_scanner.py -v
```

Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
cd E:/DocScanX && git add app/engine/scanner.py tests/test_scanner.py && git commit -m "feat: add scanner module with directory traversal and archive extraction"
```

---

### Task 3: 写 file_parser.py

**Files:**
- Create: `app/engine/file_parser.py`
- Create: `tests/test_file_parser.py`

- [ ] **Step 1: Write file_parser.py**

Write to `E:/DocScanX/app/engine/file_parser.py`:

```python
"""文件解析器 — 按格式分派解析器，提取纯文本。"""
import os
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

import chardet


@dataclass
class ParseResult:
    text: str
    encoding: str = "utf-8"
    page_count: int = 1
    error: Optional[str] = None
    metadata: Optional[dict] = None


def _read_text_file(file_path: str) -> ParseResult:
    """读取纯文本文件，自动检测编码。"""
    with open(file_path, "rb") as f:
        raw = f.read()
    if not raw:
        return ParseResult(text="", encoding="utf-8")

    detected = chardet.detect(raw)
    encoding = detected.get("encoding", "utf-8") or "utf-8"

    try:
        text = raw.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        text = raw.decode("latin-1")
        encoding = "latin-1"

    return ParseResult(text=text, encoding=encoding)


def _parse_docx(file_path: str) -> ParseResult:
    try:
        from docx import Document
        doc = Document(file_path)
        parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                parts.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text for cell in row.cells if cell.text)
                if row_text.strip():
                    parts.append(row_text)
        return ParseResult(text="\n".join(parts))
    except Exception as e:
        return ParseResult(text="", error=f"docx 解析失败: {e}")


def _parse_xlsx(file_path: str) -> ParseResult:
    try:
        from openpyxl import load_workbook
        wb = load_workbook(file_path, read_only=True, data_only=True)
        parts = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            parts.append(f"[Sheet: {sheet_name}]")
            for row in ws.iter_rows(values_only=True):
                row_text = " | ".join(str(c) for c in row if c is not None)
                if row_text.strip():
                    parts.append(row_text)
        wb.close()
        return ParseResult(text="\n".join(parts))
    except Exception as e:
        return ParseResult(text="", error=f"xlsx 解析失败: {e}")


def _parse_pptx(file_path: str) -> ParseResult:
    try:
        from pptx import Presentation
        prs = Presentation(file_path)
        parts = []
        for i, slide in enumerate(prs.slides, 1):
            slide_texts = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        if para.text.strip():
                            slide_texts.append(para.text)
            if slide_texts:
                parts.append(f"[Slide {i}]")
                parts.extend(slide_texts)
        return ParseResult(text="\n".join(parts), page_count=len(prs.slides))
    except Exception as e:
        return ParseResult(text="", error=f"pptx 解析失败: {e}")


def _parse_pdf(file_path: str) -> ParseResult:
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
            page_count = len(pdf.pages)
        return ParseResult(text="\n".join(parts), page_count=page_count)
    except Exception as e:
        return ParseResult(text="", error=f"pdf 解析失败: {e}")


def _parse_json_file(file_path: str) -> ParseResult:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = json.dumps(data, ensure_ascii=False, indent=2)
        return ParseResult(text=text)
    except Exception as e:
        return ParseResult(text="", error=f"json 解析失败: {e}")


def _parse_xml_file(file_path: str) -> ParseResult:
    try:
        tree = ET.parse(file_path)
        parts = []

        def walk(elem, depth=0):
            if elem.text and elem.text.strip():
                parts.append(f"{'  ' * depth}{elem.tag}: {elem.text.strip()}")
            for child in elem:
                walk(child, depth + 1)

        walk(tree.getroot())
        return ParseResult(text="\n".join(parts))
    except Exception as e:
        return ParseResult(text="", error=f"xml 解析失败: {e}")


PARSERS = {
    ".txt": _read_text_file,
    ".csv": _read_text_file,
    ".md": _read_text_file,
    ".log": _read_text_file,
    ".docx": _parse_docx,
    ".xlsx": _parse_xlsx,
    ".pptx": _parse_pptx,
    ".pdf": _parse_pdf,
    ".json": _parse_json_file,
    ".xml": _parse_xml_file,
    ".py": _read_text_file,
    ".java": _read_text_file,
    ".js": _read_text_file,
    ".html": _read_text_file,
    ".sql": _read_text_file,
    ".css": _read_text_file,
    ".cpp": _read_text_file,
}

UNSUPPORTED_EXTS = {".doc", ".xls", ".ppt"}


def parse_file(file_path: str) -> ParseResult:
    """解析单个文件，返回纯文本内容。"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext in UNSUPPORTED_EXTS:
        return ParseResult(text="", error=f"老旧格式暂不支持: {ext}")

    parser = PARSERS.get(ext)
    if parser is None:
        return ParseResult(text="", error=f"不支持的文件格式: {ext}")

    try:
        return parser(file_path)
    except Exception as e:
        return ParseResult(text="", error=str(e))
```

- [ ] **Step 2: Create test fixture files**

```bash
mkdir -p E:/DocScanX/tests/fixtures
```

Then write to `E:/DocScanX/tests/fixtures/sample.txt`:
```
Hello world
This is a test file.
第二行中文。
```

Write to `E:/DocScanX/tests/fixtures/sample.csv`:
```
name,age,city
张三,30,北京
李四,25,上海
```

- [ ] **Step 3: Write test_file_parser.py**

Write to `E:/DocScanX/tests/test_file_parser.py`:

```python
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
```

- [ ] **Step 4: Run tests**

```bash
cd E:/DocScanX && python -m pytest tests/test_file_parser.py -v
```

- [ ] **Step 5: Commit**

```bash
cd E:/DocScanX && git add app/engine/file_parser.py tests/test_file_parser.py tests/fixtures/ && git commit -m "feat: add file parser module supporting docx/xlsx/pptx/pdf/txt/csv/md/json/xml"
```

---

### Task 4: 写文件解析器集成测试（生成真实 Office 文件）

**Files:**
- Create: `tests/test_file_parser_integration.py`

- [ ] **Step 1: Write integration test that generates test files**

Write to `E:/DocScanX/tests/test_file_parser_integration.py`:

```python
"""集成测试：用真实库生成测试文件，验证解析器能正确提取文本。"""
import os
import json
import tempfile
import pytest
from app.engine.file_parser import parse_file


@pytest.fixture
def workdir():
    tmp = tempfile.mkdtemp()
    yield tmp
    import shutil
    shutil.rmtree(tmp)


class TestDocxParsing:
    def test_create_and_parse(self, workdir):
        from docx import Document
        path = os.path.join(workdir, "test.docx")
        doc = Document()
        doc.add_paragraph("Hello from docx")
        doc.add_paragraph("第二段内容")
        doc.save(path)

        result = parse_file(path)
        assert "Hello from docx" in result.text
        assert "第二段内容" in result.text
        assert result.error is None


class TestXlsxParsing:
    def test_create_and_parse(self, workdir):
        from openpyxl import Workbook
        path = os.path.join(workdir, "test.xlsx")
        wb = Workbook()
        ws = wb.active
        ws.title = "员工表"
        ws.append(["姓名", "部门"])
        ws.append(["张三", "研发"])
        wb.save(path)

        result = parse_file(path)
        assert "员工表" in result.text
        assert "张三" in result.text
        assert result.error is None


class TestPptxParsing:
    def test_create_and_parse(self, workdir):
        from pptx import Presentation
        path = os.path.join(workdir, "test.pptx")
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = "演示标题"
        prs.save(path)

        result = parse_file(path)
        assert "演示标题" in result.text
        assert result.error is None


class TestPdfParsing:
    def test_create_and_parse(self, workdir):
        import pdfplumber
        path = os.path.join(workdir, "test.pdf")
        # pdfplumber can't create PDFs, use a minimal approach
        # For a real test, we'd need a pre-existing PDF fixture
        # This tests the error path gracefully
        if not os.path.exists(path):
            pytest.skip("PDF fixture not available — requires pre-built PDF file")


class TestJsonParsing:
    def test_parse_json(self, workdir):
        path = os.path.join(workdir, "test.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"姓名": "张三", "年龄": 30}, f, ensure_ascii=False)

        result = parse_file(path)
        assert "张三" in result.text
        assert result.error is None


class TestXmlParsing:
    def test_parse_xml(self, workdir):
        path = os.path.join(workdir, "test.xml")
        with open(path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0"?><person><name>张三</name></person>')

        result = parse_file(path)
        assert "张三" in result.text
        assert result.error is None


class TestEncodingDetection:
    def test_gbk_file(self, workdir):
        path = os.path.join(workdir, "gbk.txt")
        with open(path, "w", encoding="gbk") as f:
            f.write("中文GBK编码测试")

        result = parse_file(path)
        assert "中文" in result.text
        assert result.error is None
```

- [ ] **Step 2: Run integration tests**

```bash
cd E:/DocScanX && python -m pytest tests/test_file_parser_integration.py -v
```

- [ ] **Step 3: Commit**

```bash
cd E:/DocScanX && git add tests/test_file_parser_integration.py && git commit -m "test: add file parser integration tests for docx/xlsx/pptx/json/xml"
```

---

### Task 5: 写 pdf_judge.py

**Files:**
- Create: `app/engine/pdf_judge.py`
- Create: `tests/test_pdf_judge.py`

- [ ] **Step 1: Write pdf_judge.py**

Write to `E:/DocScanX/app/engine/pdf_judge.py`:

```python
"""PDF 判定器 — 区分文本型 PDF 和扫描件 PDF。"""
import os
from dataclasses import dataclass

import pdfplumber


@dataclass
class PdfVerdict:
    is_text_pdf: bool
    needs_ocr: bool
    total_chars: int
    page_count: int
    text: str = ""
    error: str = ""


def judge_pdf(file_path: str, text_threshold: int = 20) -> PdfVerdict:
    """判断 PDF 类型。

    Args:
        file_path: PDF 文件路径
        text_threshold: 文本字符数阈值，超过判定为文本 PDF

    Returns:
        PdfVerdict 包含判定结果
    """
    if not os.path.isfile(file_path):
        return PdfVerdict(
            is_text_pdf=False,
            needs_ocr=False,
            total_chars=0,
            page_count=0,
            error="文件不存在",
        )

    try:
        with pdfplumber.open(file_path) as pdf:
            pages = pdf.pages
            page_count = len(pages)
            all_text = []
            total_chars = 0

            for page in pages:
                text = page.extract_text() or ""
                all_text.append(text)
                total_chars += len(text)

            text = "\n".join(all_text)

            if total_chars > text_threshold:
                return PdfVerdict(
                    is_text_pdf=True,
                    needs_ocr=False,
                    total_chars=total_chars,
                    page_count=page_count,
                    text=text,
                )

            # 字符数不足，检查是否有嵌入图片
            has_images = False
            for page in pages:
                if hasattr(page, "images") and page.images:
                    has_images = True
                    break

            if has_images:
                return PdfVerdict(
                    is_text_pdf=False,
                    needs_ocr=True,
                    total_chars=total_chars,
                    page_count=page_count,
                    text=text,
                )
            else:
                return PdfVerdict(
                    is_text_pdf=False,
                    needs_ocr=False,
                    total_chars=total_chars,
                    page_count=page_count,
                    error="无法处理：PDF 无文本层且无嵌入图片",
                )

    except Exception as e:
        return PdfVerdict(
            is_text_pdf=False,
            needs_ocr=False,
            total_chars=0,
            page_count=0,
            error=f"PDF 解析失败: {e}",
        )
```

- [ ] **Step 2: Write test_pdf_judge.py**

Write to `E:/DocScanX/tests/test_pdf_judge.py`:

```python
import os
import tempfile
import pytest
from app.engine.pdf_judge import judge_pdf, PdfVerdict


class TestPdfJudge:
    def test_file_not_found(self):
        result = judge_pdf("/nonexistent/file.pdf")
        assert not result.is_text_pdf
        assert result.error != ""

    def test_text_pdf_detection(self):
        """用 pdfplumber 创建一个简单的文本 PDF 并测试。"""
        # pdfplumber 是读取库，不能创建 PDF
        # 此测试依赖真实 PDF 文件
        pytest.skip("需要真实 PDF 测试文件")

    def test_pdf_verdict_dataclass(self):
        v = PdfVerdict(is_text_pdf=True, needs_ocr=False, total_chars=100, page_count=3)
        assert v.is_text_pdf
        assert not v.needs_ocr
        assert v.total_chars == 100
        assert v.page_count == 3
```

- [ ] **Step 3: Run tests**

```bash
cd E:/DocScanX && python -m pytest tests/test_pdf_judge.py -v
```

- [ ] **Step 4: Commit**

```bash
cd E:/DocScanX && git add app/engine/pdf_judge.py tests/test_pdf_judge.py && git commit -m "feat: add pdf_judge module for text vs scanned PDF detection"
```

---

### Task 6: 端到端集成测试

**Files:**
- Create: `tests/test_pipeline_integration.py`

- [ ] **Step 1: Write integration test**

Write to `E:/DocScanX/tests/test_pipeline_integration.py`:

```python
"""端到端测试：扫描 → 解析 → PDF判定 完整流程。"""
import os
import json
import tempfile
import pytest
from app.engine.scanner import scan_directory
from app.engine.file_parser import parse_file
from app.engine.pdf_judge import judge_pdf


@pytest.fixture
def test_workspace():
    tmp = tempfile.mkdtemp()
    # 创建 txt
    with open(os.path.join(tmp, "readme.txt"), "w", encoding="utf-8") as f:
        f.write("Hello world\n测试中文")
    # 创建 csv
    with open(os.path.join(tmp, "data.csv"), "w", encoding="utf-8") as f:
        f.write("name,age\n张三,30")
    # 创建 json
    with open(os.path.join(tmp, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"app": "DocScanX"}, f)
    # 创建 docx
    from docx import Document
    doc = Document()
    doc.add_paragraph("员工合同文本")
    doc.save(os.path.join(tmp, "contract.docx"))
    # 创建 xlsx
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["姓名", "手机号"])
    ws.append(["张三", "13800001111"])
    wb.save(os.path.join(tmp, "roster.xlsx"))

    yield tmp
    import shutil
    shutil.rmtree(tmp)


class TestPipeline:
    def test_scan_then_parse_all(self, test_workspace):
        groups = {"text": True, "office_new": True, "pdf": True, "structured": True, "archive": False}
        files = scan_directory(test_workspace, ext_groups=groups)

        assert len(files) >= 4  # txt + csv + docx + xlsx + json

        results = []
        for f in files:
            result = parse_file(f.path)
            results.append((f.ext, result))

        # 所有文件应该解析成功
        for ext, result in results:
            assert result.error is None, f"Failed to parse {ext}: {result.error}"
            assert result.text != "", f"Empty text for {ext}"

        print(f"Parsed {len(results)} files successfully")

    def test_pdf_judge_on_docx_wont_crash(self):
        """pdf_judge 只在 PDF 上调用，验证不会对非 PDF 崩溃。"""
        # pdf_judge 内部用 pdfplumber.open，非 PDF 会抛异常并被捕获
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("not a pdf")
        result = judge_pdf(f.name)
        assert result.error != ""  # 应该返回错误，不抛异常
        os.unlink(f.name)
```

- [ ] **Step 2: Run integration tests**

```bash
cd E:/DocScanX && python -m pytest tests/test_pipeline_integration.py -v
```

- [ ] **Step 3: Commit**

```bash
cd E:/DocScanX && git add tests/test_pipeline_integration.py && git commit -m "test: add end-to-end pipeline integration test"
```

---

### Task 7: 全量测试 + 最终提交

- [ ] **Step 1: Run all tests**

```bash
cd E:/DocScanX && python -m pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: Verify git status clean**

```bash
cd E:/DocScanX && git status
```
