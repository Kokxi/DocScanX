"""OCR 引擎 — 基于 RapidOCR ONNX 模型。

支持图片和 PDF 输入，输出识别文本及文字块坐标。
"""
import os
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

import fitz  # PyMuPDF
from rapidocr_onnxruntime import RapidOCR

from app.utils.model_utils import get_ocr_model_dir

logger = logging.getLogger("system")

_ocr_instance: Optional[RapidOCR] = None


def _get_ocr_engine() -> RapidOCR:
    """懒初始化 OCR 引擎（单例）。"""
    global _ocr_instance
    if _ocr_instance is None:
        ocr_dir = get_ocr_model_dir(None)
        det = os.path.join(ocr_dir, "ch_PP-OCRv3_det_infer.onnx")
        rec = os.path.join(ocr_dir, "ch_PP-OCRv3_rec_infer.onnx")
        cls = os.path.join(ocr_dir, "ch_ppocr_mobile_v2.0_cls_infer.onnx")
        _ocr_instance = RapidOCR(
            det_model_path=det,
            rec_model_path=rec,
            cls_model_path=cls,
        )
        logger.info(f"OCR 引擎初始化完成 (det={os.path.basename(det)})")
    return _ocr_instance


@dataclass
class OcrBlock:
    text: str
    confidence: float
    bbox: list  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]


@dataclass
class OcrResult:
    text: str = ""
    blocks: list = field(default_factory=list)  # list[OcrBlock]
    page_count: int = 1
    elapsed: float = 0.0
    error: Optional[str] = None


def ocr_image(image_path: str, min_confidence: float = 0.5) -> OcrResult:
    """对单张图片执行 OCR。

    Args:
        image_path: 图片文件路径
        min_confidence: 最低置信度阈值，低于此值的文字块被丢弃

    Returns:
        OcrResult: 识别结果
    """
    if not os.path.exists(image_path):
        return OcrResult(error=f"文件不存在: {image_path}")

    start = time.time()
    try:
        engine = _get_ocr_engine()
        raw, elapse = engine(image_path)
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"OCR 失败 [{image_path}]: {e}")
        return OcrResult(error=str(e), elapsed=elapsed)

    blocks = []
    lines = []
    if raw:
        for item in raw:
            bbox, text, conf_str = item
            conf = float(conf_str) if isinstance(conf_str, str) else conf_str
            if conf < min_confidence:
                continue
            blocks.append(OcrBlock(text=text, confidence=conf, bbox=bbox))
            lines.append(text)

    return OcrResult(
        text="\n".join(lines),
        blocks=blocks,
        page_count=1,
        elapsed=time.time() - start,
    )


def ocr_pdf_page(pdf_path: str, page_num: int = 0, dpi: int = 200,
                 min_confidence: float = 0.5) -> OcrResult:
    """对 PDF 单页执行 OCR（渲染为图片后识别）。

    Args:
        pdf_path: PDF 文件路径
        page_num: 页码（0-based）
        dpi: 渲染分辨率
        min_confidence: 最低置信度阈值
    """
    if not os.path.exists(pdf_path):
        return OcrResult(error=f"文件不存在: {pdf_path}")

    start = time.time()
    try:
        doc = fitz.open(pdf_path)
        if page_num >= len(doc):
            doc.close()
            return OcrResult(error=f"页码超出范围: {page_num} (共 {len(doc)} 页)")
        page = doc[page_num]
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        doc.close()

        # 保存为临时 PNG
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            pix.save(f.name)
            tmp_path = f.name

        result = ocr_image(tmp_path, min_confidence)
        os.unlink(tmp_path)
        result.elapsed = time.time() - start
        result.page_count = 1
        return result
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"OCR PDF 失败 [{pdf_path} p{page_num}]: {e}")
        return OcrResult(error=str(e), elapsed=elapsed)


def ocr_pdf(pdf_path: str, dpi: int = 200, min_confidence: float = 0.5,
            max_pages: int = 100) -> OcrResult:
    """对 PDF 全部页面执行 OCR。

    Args:
        pdf_path: PDF 文件路径
        dpi: 渲染分辨率
        min_confidence: 最低置信度阈值
        max_pages: 最大处理页数
    """
    if not os.path.exists(pdf_path):
        return OcrResult(error=f"文件不存在: {pdf_path}")

    start = time.time()
    try:
        doc = fitz.open(pdf_path)
        total = min(len(doc), max_pages)
        all_lines = []
        all_blocks = []

        for i in range(total):
            page_result = ocr_pdf_page(pdf_path, i, dpi, min_confidence)
            if page_result.error:
                doc.close()
                return OcrResult(error=f"第{i}页OCR失败: {page_result.error}")
            all_lines.append(page_result.text)
            all_blocks.extend(page_result.blocks)

        doc.close()
        return OcrResult(
            text="\n".join(all_lines),
            blocks=all_blocks,
            page_count=total,
            elapsed=time.time() - start,
        )
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"OCR PDF 失败 [{pdf_path}]: {e}")
        return OcrResult(error=str(e), elapsed=elapsed)
