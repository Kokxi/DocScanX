"""文件系统工具函数。"""
import os


def ensure_dir(dir_path: str) -> str:
    """确保目录存在，不存在则创建。返回目录路径。"""
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def get_file_size_mb(file_path: str) -> float:
    """获取文件大小（MB）。"""
    return os.path.getsize(file_path) / (1024 * 1024)


def is_file_accessible(file_path: str) -> bool:
    """检查文件是否存在且可读。"""
    return os.path.isfile(file_path) and os.access(file_path, os.R_OK)
