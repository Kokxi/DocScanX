# DocScanX Phase 2A — 文件处理管线设计

> 日期：2026-06-02 | 状态：进行中

## 目标

实现文件发现 → 格式解析 → PDF判定 的完整管线，输出每个文件的纯文本内容，供 OCR/UIE 模块消费。

## 模块

### 1. scanner.py — 目录扫描器

**职责**：遍历目录、发现文件、解压压缩包、按后缀过滤。

**输入**：目录路径 + 配置（include_subdir, extract_archive, file_extensions, extension_groups_default）
**输出**：`List[FileInfo]`，每个 FileInfo 包含 path, ext, size_mb

```python
@dataclass
class FileInfo:
    path: str          # 绝对路径
    ext: str           # 后缀（小写），如 ".docx"
    size_mb: float     # 文件大小
    is_archive: bool   # 是否压缩包
```

**流程**：
```
输入目录 → os.walk（可选递归）
    → 按后缀过滤（按 extension_groups_default 判断各分组是否启用）
    → 发现压缩包 → 解压到 temp/unpacked/{task_id}/
    → 递归扫描解压目录中的文件（也按后缀过滤）
    → 返回文件清单
```

**压缩包解压**：
- .zip: zipfile 内置
- .rar: patool 或 rarfile（可选依赖，不存在时跳过 .rar 并记录警告）
- .7z: patool（同上）
- 解压失败：记录警告，跳过该压缩包

**边界**：
- 嵌套压缩包最多 3 层
- 单文件超过 500MB 跳过并警告
- 空目录不报错

### 2. file_parser.py — 文件解析器

**职责**：按格式分派解析器，提取纯文本。

**接口**：
```python
def parse_file(file_path: str) -> ParseResult:
    # 返回 {"text": str, "encoding": str, "page_count": int, "metadata": dict}
```

**解析器表**：

| 格式 | 库 | 方法 |
|------|------|------|
| .docx | python-docx | 遍历 paragraphs + tables |
| .xlsx | openpyxl | 遍历所有 sheet 的 cells，按行拼接 |
| .pptx | python-pptx | 遍历 slides 的 shapes，提取文本框 |
| .pdf | pdfplumber | 先提取文本层（pdf_judge 判定在前） |
| .txt/.csv/.md/.log | 内置 open | 读文件 + chardet 编码检测 |
| .json | json | 格式化输出 key-value |
| .xml | xml.etree | 提取所有 text 节点 |
| .doc/.xls/.ppt | 跳过 | 记录"老旧格式暂不支持" |
| .py/.java/.js 等 | 内置 open | 开发类文件，config 控制是否解析 |

**异常处理**：
- 文件损坏/加密：返回 ParseResult(text="", error="文件损坏/加密")
- 编码检测失败：降级 latin-1
- 单文件超时 300s：抛出后由调度层捕获

**依赖新增**：
```
python-docx>=0.8.11
openpyxl>=3.1.0
python-pptx>=0.6.21
pdfplumber>=0.9.0
chardet>=5.0
```

### 3. pdf_judge.py — PDF 判定器

**职责**：判断 PDF 是文本型还是扫描件型。

**判定逻辑**：
1. 用 pdfplumber 打开 PDF
2. 检测每页文本字符数
3. 如果总字符数 > text_threshold（默认 20）→ 文本 PDF
4. 否则检查是否有嵌入图片
5. 有图片 → 扫描件 PDF（标记走 OCR）
6. 无图片 → 无法处理

**输出**：
```python
@dataclass
class PdfVerdict:
    is_text_pdf: bool
    needs_ocr: bool
    total_chars: int
    page_count: int
    text: str          # 如果 is_text_pdf，包含提取的文本
```

## 测试要求

每个模块至少覆盖：
- scanner: 正常目录、空目录、压缩包、嵌套压缩包、后缀过滤
- file_parser: 每种支持格式一个样本文件
- pdf_judge: 文本 PDF、扫描件 PDF（用 mock）

测试数据放在 `tests/fixtures/` 目录。

## 不在 Scope

- OCR 引擎
- UIE 信息抽取
- IPE 引擎
- 任何 ML 模型加载
- 前端页面
- 任务调度（scanner 和 parser 独立调用即可，不在此 Phase 做管线编排）

## 验证标准

1. scanner 扫描测试目录，返回正确的文件清单
2. file_parser 解析 docx/xlsx/pptx/pdf/txt 各返回非空文本
3. pdf_judge 正确区分文本 PDF 和扫描件 PDF
4. 损坏文件/不支持格式不中断流程，返回 error 标记
5. 压缩包解压后内部文件被正确发现
