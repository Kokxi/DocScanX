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
