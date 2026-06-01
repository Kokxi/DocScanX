"""日志系统初始化。

提供三种日志通道：
- system: 系统事件（启动/停止/配置变更），输出到控制台 + logs/system.log
- task: 任务处理记录，输出到 logs/task.log
- audit: 操作审计，输出到 logs/audit.log
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from app.utils.file_utils import ensure_dir

_loggers_initialized = False

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _create_rotating_handler(
    filepath: str, max_bytes: int, backup_count: int = 5
) -> RotatingFileHandler:
    """创建滚動文件 handler。"""
    ensure_dir(os.path.dirname(filepath))
    handler = RotatingFileHandler(
        filepath, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    return handler


def setup_logging(log_dir: str = "./logs", max_size_mb: int = 10, level: str = "INFO") -> None:
    """初始化全局日志系统。"""
    global _loggers_initialized
    if _loggers_initialized:
        return

    max_bytes = max_size_mb * 1024 * 1024
    log_level = getattr(logging, level.upper(), logging.INFO)

    # System logger — 控制台 + 文件
    system_logger = logging.getLogger("system")
    system_logger.setLevel(log_level)
    system_logger.propagate = False

    # 控制台 handler
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    console.setLevel(log_level)
    system_logger.addHandler(console)

    # 文件 handler
    system_logger.addHandler(_create_rotating_handler(
        os.path.join(log_dir, "system.log"), max_bytes
    ))

    # Task logger — 仅文件
    task_logger = logging.getLogger("task")
    task_logger.setLevel(log_level)
    task_logger.propagate = False
    task_logger.addHandler(_create_rotating_handler(
        os.path.join(log_dir, "task.log"), max_bytes
    ))

    # Audit logger — 仅文件
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False
    audit_logger.addHandler(_create_rotating_handler(
        os.path.join(log_dir, "audit.log"), max_bytes
    ))

    _loggers_initialized = True
    system_logger.info("日志系统初始化完成")


def get_system_logger() -> logging.Logger:
    return logging.getLogger("system")


def get_task_logger() -> logging.Logger:
    return logging.getLogger("task")


def get_audit_logger() -> logging.Logger:
    return logging.getLogger("audit")
