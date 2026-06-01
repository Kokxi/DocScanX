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
