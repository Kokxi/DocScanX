"""远程扫描 API。"""
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Request

from app.engine.remote import (RemoteSource, scan_remote_source,
                                connect_ftp, list_ftp_files)
from app.engine.report import save_report
from app.core import config as config_module

logger = logging.getLogger("system")
audit = logging.getLogger("audit")
router = APIRouter()

_tz = timezone(timedelta(hours=8))
_scan_status: dict = {}


def _output_dir():
    cfg = config_module.config
    return getattr(cfg.path, "output_dir", "./output") if cfg else "./output"


@router.post("/remote/test")
async def test_remote_connection(request: Request):
    """测试远程 FTP 服务器连接。"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    source = RemoteSource(
        name=body.get("name", "Test"),
        protocol=body.get("protocol", "ftp"),
        host=body.get("host", ""),
        port=body.get("port", 21),
        username=body.get("username", ""),
        password=body.get("password", ""),
        base_path=body.get("base_path", "/"),
        connect_timeout=body.get("connect_timeout", 15),
    )

    if not source.host:
        return {"code": 1, "message": "请输入服务器地址"}

    try:
        with connect_ftp(source) as ftp:
            files = list_ftp_files(ftp, source.base_path)
            return {"code": 0, "data": {
                "file_count": len(files),
                "message": f"连接成功，共发现 {len(files)} 个文件"
            }}
    except Exception as e:
        return {"code": 1, "message": f"连接失败: {e}"}


@router.post("/remote/scan")
async def start_remote_scan(request: Request):
    """启动远程 FTP 扫描任务。"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    task_name = body.get("name", "")
    ext_groups = body.get("ext_groups")
    mask_enabled = body.get("mask_enabled", True)

    source = RemoteSource(
        name=task_name or "Remote-Scan",
        protocol=body.get("protocol", "ftp"),
        host=body.get("host", ""),
        port=body.get("port", 21),
        username=body.get("username", ""),
        password=body.get("password", ""),
        base_path=body.get("base_path", "/"),
        max_file_size_mb=body.get("max_file_size_mb", 500),
        connect_timeout=body.get("connect_timeout", 30),
    )

    if not source.host:
        return {"code": 1, "message": "请输入服务器地址"}

    task_id = datetime.now(_tz).strftime("%Y%m%d_%H%M%S")
    _scan_status[task_id] = {"status": "running", "progress": 0,
                              "result": None, "error": None}

    try:
        result = scan_remote_source(
            source=source,
            ext_groups=ext_groups,
            mask_enabled=mask_enabled,
        )

        report_id = save_report(result, _output_dir(),
                                task_name=task_name or source.name)

        _scan_status[task_id] = {
            "status": "done", "progress": 100,
            "report_id": report_id,
            "total_files": len(result.files),
            "total_persons": result.total_persons,
            "error": None,
        }
        audit.info(f"远程扫描完成: {task_name or source.name} "
                   f"({len(result.files)}文件, {result.total_persons}人)")

        return {
            "code": 0,
            "data": {
                "task_id": task_id,
                "report_id": report_id,
                "total_files": len(result.files),
                "total_persons": result.total_persons,
            },
        }
    except Exception as e:
        logger.error(f"远程扫描失败: {e}")
        _scan_status[task_id] = {"status": "error", "progress": 0,
                                 "error": str(e)}
        return {"code": 1, "message": str(e)}
