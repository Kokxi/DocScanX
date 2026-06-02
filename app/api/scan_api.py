"""扫描任务 API。"""
import os
import shutil
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Request, UploadFile, File

from app.core import config as config_module
from app.engine.pipeline import process_directory, process_file
from app.engine.report import save_report

logger = logging.getLogger("system")
audit = logging.getLogger("audit")
router = APIRouter()
_tz = timezone(timedelta(hours=8))

_scan_status: dict = {}  # task_id -> {status, progress, result, error}


def _output_dir():
    cfg = config_module.config
    return getattr(cfg.path, "output_dir", "./output") if cfg else "./output"


@router.post("/scan/start")
async def start_scan(request: Request):
    """启动扫描任务。"""
    try:
        body = await request.json()
    except Exception:
        body = {}
    dir_path = body.get("path", "")
    task_name = body.get("name", "")
    include_subdir = body.get("include_subdir", True)
    extract_archive = body.get("extract_archive", True)
    cfg_default_mask = getattr(getattr(config_module.config, "inference", None), "mask_enabled", True) if config_module.config else True
    mask_enabled = body.get("mask_enabled", cfg_default_mask)
    ext_groups = body.get("ext_groups")
    if ext_groups and isinstance(ext_groups, dict) and not any(ext_groups.values()):
        ext_groups = None

    if not dir_path or not (os.path.isdir(dir_path) or os.path.isfile(dir_path)):
        return {"code": 1, "message": f"路径不存在: {dir_path}"}

    task_id = datetime.now(_tz).strftime("%Y%m%d_%H%M%S")
    _scan_status[task_id] = {"status": "running", "progress": 0, "result": None, "error": None}

    try:
        if os.path.isfile(dir_path):
            # 单文件扫描
            ext = os.path.splitext(dir_path)[1].lower()
            size_mb = os.path.getsize(dir_path) / (1024 * 1024)
            file_result = process_file(dir_path, ext, size_mb, mask_enabled=mask_enabled)
            from app.engine.pipeline import PipelineResult
            result = PipelineResult()
            if not file_result.error:
                result.files = [file_result]
                result.total_persons = len(result.all_persons)
        else:
            result = process_directory(
                dir_path=dir_path,
                include_subdir=include_subdir,
                extract_archive=extract_archive,
                ext_groups=ext_groups,
                mask_enabled=mask_enabled,
            )
        # 保存报告
        report_id = save_report(result, _output_dir(), task_name=task_name)

        _scan_status[task_id] = {
            "status": "done",
            "progress": 100,
            "report_id": report_id,
            "total_files": len(result.files),
            "total_persons": result.total_persons,
            "error": None,
        }
        audit.info(f"扫描任务启动: {task_name or dir_path} ({len(result.files)}文件, {result.total_persons}人)")
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
        logger.error(f"扫描失败: {e}")
        _scan_status[task_id] = {"status": "error", "progress": 0, "error": str(e)}
        return {"code": 1, "message": str(e)}


@router.get("/scan/status/{task_id}")
async def scan_status(task_id: str):
    """查询扫描任务状态。"""
    s = _scan_status.get(task_id)
    if not s:
        return {"code": 1, "message": "任务不存在"}
    return {"code": 0, "data": s}


@router.post("/scan/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件到服务器临时目录，返回服务器端路径。"""
    try:
        cfg = config_module.config
        temp_dir = getattr(cfg.path, "temp_dir", "./temp") if cfg else "./temp"
        upload_dir = os.path.join(temp_dir, "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        safe_name = os.path.basename(file.filename or "uploaded_file")
        dest = os.path.join(upload_dir, safe_name)
        # 冲突时追加序号
        base, ext = os.path.splitext(safe_name)
        n = 1
        while os.path.exists(dest):
            dest = os.path.join(upload_dir, f"{base}_{n}{ext}")
            n += 1

        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        size_mb = round(os.path.getsize(dest) / (1024 * 1024), 2)

        logger.info(f"文件上传成功: {safe_name} -> {dest}")
        audit.info(f"文件上传: {safe_name} ({size_mb}MB)")
        return {"code": 0, "data": {"path": dest, "name": safe_name, "size_mb": size_mb}}
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        return {"code": 1, "message": str(e)}


@router.post("/scan/quick")
async def quick_scan(request: Request):
    """单文件快速扫描，返回实体摘要。"""
    try:
        body = await request.json()
    except Exception:
        body = {}
    file_path = body.get("path", "")

    if not file_path or not os.path.isfile(file_path):
        return {"code": 1, "message": f"文件不存在: {file_path}"}

    ext = os.path.splitext(file_path)[1].lower()
    size_mb = os.path.getsize(file_path) / (1024 * 1024)

    result = process_file(file_path, ext, size_mb)
    items = []
    if result.extraction_result:
        for e in result.extraction_result.entities:
            items.append({"type": e.type, "value": e.value, "confidence": f"{e.confidence:.0%}"})

    return {"code": 0, "data": {"file": file_path, "items": items}}


@router.post("/scan/browse-folder")
async def browse_folder():
    """打开原生文件夹选择对话框，返回所选路径。"""
    try:
        import tkinter.filedialog
        import tkinter
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = tkinter.filedialog.askdirectory(title="选择扫描文件夹")
        root.destroy()
        if folder and os.path.isdir(folder):
            return {"code": 0, "data": {"path": folder}}
        return {"code": 0, "data": {"path": ""}}
    except Exception as e:
        logger.warning(f"文件夹选择失败（可能无 GUI 环境）: {e}")
        return {"code": 1, "message": "当前环境不支持原生文件夹选择，请手动输入路径"}
