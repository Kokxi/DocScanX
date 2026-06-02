"""文件处理管线编排。

将 scan → parse → pdf_judge → OCR → UIE → validate → mask → IPE 串联为统一流程。
"""
import os
import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from app.engine.scanner import scan_directory, FileInfo
from app.engine.file_parser import parse_file, ParseResult
from app.engine.pdf_judge import judge_pdf, PdfVerdict
from app.engine.ocr import ocr_image, ocr_pdf, OcrResult
from app.engine.uie_engine import extract_entities, ExtractionResult
from app.engine.validator import filter_valid_entities
from app.engine.masking import generate_masked_report
from app.engine.ipe import parse_identities, IpeResult, Person
from app.engine.risk import add_risk_to_person

logger = logging.getLogger("system")


@dataclass
class StageTrace:
    stage: str
    status: str
    fields_count: int = 0
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class FileProcessResult:
    file_path: str
    ext: str
    size_mb: float
    parse_result: Optional[ParseResult] = None
    pdf_verdict: Optional[PdfVerdict] = None
    ocr_result: Optional[OcrResult] = None
    extraction_result: Optional[ExtractionResult] = None
    ipe_result: Optional[IpeResult] = None
    masked_report: Optional[dict] = None
    error: Optional[str] = None
    traces: List[StageTrace] = field(default_factory=list)

    @property
    def has_text(self) -> bool:
        if self.parse_result and self.parse_result.text:
            return True
        if self.ocr_result and self.ocr_result.text:
            return True
        return False

    @property
    def text(self) -> str:
        if self.parse_result and self.parse_result.text:
            return self.parse_result.text
        if self.ocr_result and self.ocr_result.text:
            return self.ocr_result.text
        return ""


@dataclass
class PipelineResult:
    files: List[FileProcessResult] = field(default_factory=list)
    total_persons: int = 0

    @property
    def all_persons(self) -> List[Person]:
        persons = []
        for f in self.files:
            if f.ipe_result:
                persons.extend(f.ipe_result.persons)
        return persons


def _trace(result: FileProcessResult, stage: str, status: str,
           fields_count: int = 0, error: str = None, t0: float = None):
    dur = (time.time() - t0) * 1000 if t0 else 0.0
    result.traces.append(StageTrace(stage=stage, status=status,
                                     fields_count=fields_count, error=error, duration_ms=dur))


def process_file(file_path: str, ext: str = "", size_mb: float = 0.0,
                 extract_schema: Optional[List[str]] = None,
                 mask_enabled: bool = True) -> FileProcessResult:
    """处理单个文件：parse → OCR → extract → validate → mask → IPE。"""
    result = FileProcessResult(file_path=file_path, ext=ext, size_mb=size_mb)

    try:
        # 1. 解析文件
        t0 = time.time()
        parsed = parse_file(file_path)
        result.parse_result = parsed
        if parsed.error:
            _trace(result, "解析", "失败", error=parsed.error, t0=t0)
            result.error = f"解析失败: {parsed.error}"
            return result
        _trace(result, "解析", "成功",
               fields_count=len(parsed.text) if parsed.text else 0, t0=t0)
        text = parsed.text

        # 2. PDF 判定 + OCR
        if ext.lower() == ".pdf":
            t0 = time.time()
            verdict = judge_pdf(file_path)
            result.pdf_verdict = verdict
            _trace(result, "PDF判定", "成功",
                   fields_count=verdict.total_chars, t0=t0)
            if verdict.needs_ocr:
                t0 = time.time()
                ocr = ocr_pdf(file_path)
                result.ocr_result = ocr
                if ocr.error:
                    _trace(result, "OCR", "失败", error=ocr.error, t0=t0)
                    result.error = f"OCR失败: {ocr.error}"
                    return result
                text = ocr.text
                _trace(result, "OCR", "成功", fields_count=len(ocr.text) if ocr.text else 0, t0=t0)

        # 3. 图片 OCR
        if not text or len(text.strip()) < 10:
            image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
            if ext.lower() in image_exts:
                t0 = time.time()
                ocr = ocr_image(file_path)
                result.ocr_result = ocr
                if ocr.error:
                    _trace(result, "OCR", "失败", error=ocr.error, t0=t0)
                    result.error = f"OCR失败: {ocr.error}"
                    return result
                text = ocr.text
                _trace(result, "OCR", "成功", fields_count=len(ocr.text) if ocr.text else 0, t0=t0)

        if not text or not text.strip():
            _trace(result, "抽取", "跳过", error="未能提取到文本内容")
            result.error = "未能提取到文本内容"
            return result

        # 4. 信息抽取
        t0 = time.time()
        extraction = extract_entities(text, schema=extract_schema)
        result.extraction_result = extraction
        _trace(result, "抽取", "成功" if extraction.entities else "跳过",
               fields_count=len(extraction.entities), t0=t0)

        if not extraction.entities:
            return result

        # 5. 实体校验 + 过滤
        t0 = time.time()
        valid_entities = filter_valid_entities(extraction.entities)
        _trace(result, "校验", "成功", fields_count=len(valid_entities), t0=t0)

        if not valid_entities:
            return result

        # 6. 脱敏
        if mask_enabled:
            t0 = time.time()
            result.masked_report = generate_masked_report(text, valid_entities)
            _trace(result, "脱敏", "成功", t0=t0)
        else:
            _trace(result, "脱敏", "跳过", error="脱敏已关闭")

        # 7. IPE 身份解析 + 风险评分
        t0 = time.time()
        result.ipe_result = parse_identities(valid_entities, source_text=text)
        for p in result.ipe_result.persons:
            add_risk_to_person(p)
        _trace(result, "IPE", "成功", fields_count=len(result.ipe_result.persons), t0=t0)

        # 8. 应用脱敏到实体和人员数据
        if mask_enabled and result.masked_report:
            t0 = time.time()
            mappings = result.masked_report.get("mappings", [])
            value_map = {m["original"]: m["masked"] for m in mappings}
            _sensitive_attrs = ["name", "id_card", "phone", "email", "bank_card",
                               "address", "wechat", "birthday", "job_no", "plate_no",
                               "passport", "gender"]
            for e in valid_entities:
                if e.value in value_map:
                    e.value = value_map[e.value]
            for p in result.ipe_result.persons:
                for attr in _sensitive_attrs:
                    val = getattr(p, attr, "")
                    if val and val in value_map:
                        setattr(p, attr, value_map[val])
            _trace(result, "脱敏应用", "成功", t0=t0)

    except Exception as e:
        logger.error(f"处理文件失败 [{file_path}]: {e}")
        result.error = str(e)

    return result


def process_directory(dir_path: str, include_subdir: bool = True,
                      extract_archive: bool = True,
                      extract_schema: Optional[List[str]] = None,
                      ext_groups: Optional[dict] = None,
                      mask_enabled: bool = True) -> PipelineResult:
    """扫描并处理目录中所有文件。"""
    logger.info(f"开始处理目录: {dir_path}")

    files = scan_directory(
        root_path=dir_path,
        include_subdir=include_subdir,
        extract_archive=extract_archive,
        ext_groups=ext_groups,
    )

    if not files:
        logger.warning(f"目录无匹配文件: {dir_path}")
        return PipelineResult()

    results = PipelineResult()
    for fi in files:
        if not os.path.isfile(fi.path):
            continue
        logger.info(f"处理文件 [{fi.ext}]: {fi.path}")
        fr = process_file(fi.path, fi.ext, fi.size_mb, extract_schema, mask_enabled=mask_enabled)
        results.files.append(fr)

    results.total_persons = len(results.all_persons)
    logger.info(f"目录处理完成: {len(results.files)} 文件, {results.total_persons} 人")

    return results
