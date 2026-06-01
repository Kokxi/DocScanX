"""文本处理工具函数。"""


def truncate(text: str, max_len: int = 100) -> str:
    """截断文本到指定长度，超出加省略号。"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def safe_str(obj) -> str:
    """安全转换为字符串，避免 None / 编码异常。"""
    if obj is None:
        return ""
    return str(obj)
