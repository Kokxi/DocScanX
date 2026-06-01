"""日志查询服务。

从日志文件中读取、解析、过滤、分页返回日志条目。
"""
import os
import re
from typing import Optional

LOG_PATTERN = re.compile(
    r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\] \[([^\]]+)\] (.+)"
)


def _parse_log_line(line: str) -> Optional[dict]:
    """解析单行日志，返回 dict 或 None（非标准格式行）。"""
    m = LOG_PATTERN.match(line.strip())
    if not m:
        return None
    return {
        "time": m.group(1),
        "level": m.group(2),
        "name": m.group(3),
        "message": m.group(4),
    }


def query_logs(
    filename: str,
    log_dir: str = "./logs",
    page: int = 1,
    page_size: int = 20,
    level: Optional[str] = None,
    name: Optional[str] = None,
    search: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> dict:
    """分页查询日志文件。

    Args:
        filename: 日志文件名（不含路径），如 "system.log"
        log_dir: 日志目录
        page: 页码（从 1 开始）
        page_size: 每页条数
        level: 级别过滤（DEBUG/INFO/WARNING/ERROR）
        name: 日志名称过滤（如 "system", "task", "audit"）
        search: 关键词搜索
        start_time: 起始时间（字符串比较）
        end_time: 结束时间（字符串比较）

    Returns:
        {"items": [...], "total": int, "page": int, "page_size": int}
    """
    filepath = os.path.join(log_dir, filename)
    if not os.path.isfile(filepath):
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    # 读取全部行并解析（日志文件通常不大，全量读入内存）
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    entries = []
    for line in lines:
        entry = _parse_log_line(line)
        if entry is None:
            continue
        # 过滤
        if level and entry["level"].upper() != level.upper():
            continue
        if name and entry["name"] != name:
            continue
        if start_time and entry["time"] < start_time:
            continue
        if end_time and entry["time"] > end_time:
            continue
        if search and search.lower() not in entry["message"].lower():
            continue
        entries.append(entry)

    # 倒序（最新在前）
    entries.reverse()

    total = len(entries)
    start = (page - 1) * page_size
    end = start + page_size
    items = entries[start:end]

    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_available_logs(log_dir: str = "./logs") -> list:
    """返回日志目录下可查询的日志文件列表。"""
    if not os.path.isdir(log_dir):
        return []
    return sorted([f for f in os.listdir(log_dir) if f.endswith(".log")])
