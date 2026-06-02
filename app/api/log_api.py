"""日志查询 API 端点。"""
import json
import os

from fastapi import APIRouter, Query

from app.core import config as config_module
from app.services.log_service import get_available_logs, query_logs

router = APIRouter()


@router.get("/logs/files")
async def list_log_files():
    """获取可用日志文件列表。"""
    files = get_available_logs()
    return {"code": 0, "data": files, "message": "ok"}


@router.get("/logs")
async def get_logs(
    file: str = Query("system.log", description="日志文件名"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    level: str = Query(None, description="级别过滤: DEBUG/INFO/WARNING/ERROR"),
    name: str = Query(None, description="日志名称过滤: system/task/audit"),
    search: str = Query(None, description="关键词搜索"),
    start_time: str = Query(None, description="起始时间"),
    end_time: str = Query(None, description="结束时间"),
):
    """分页查询日志。"""
    result = query_logs(
        filename=file,
        page=page,
        page_size=page_size,
        level=level,
        name=name,
        search=search,
        start_time=start_time,
        end_time=end_time,
    )
    return {"code": 0, "data": result, "message": "ok"}


@router.get("/logs/trace")
async def get_file_traces(report_id: str = Query(..., description="报告ID")):
    """获取指定报告的文件处理轨迹。"""
    cfg = config_module.config
    output_dir = getattr(cfg.path, "output_dir", "./output") if cfg else "./output"
    json_path = os.path.join(output_dir, report_id, "report.json")

    if not os.path.exists(json_path):
        return {"code": 1, "message": "报告不存在"}

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    traces = []
    for fl in data.get("files", []):
        file_traces = fl.get("traces", [])
        if not file_traces:
            # 无 trace 数据时，基于文件状态生成简单轨迹
            if fl.get("error"):
                traces.append({"path": fl["path"], "stage": "处理", "status": "失败",
                               "fields": "-", "error": fl.get("error", "")})
            else:
                traces.append({"path": fl["path"], "stage": "处理", "status": "成功",
                               "fields": f"{len(fl.get('entities', []))}项", "error": ""})
        else:
            for t in file_traces:
                traces.append({
                    "path": fl["path"],
                    "stage": t["stage"],
                    "status": t["status"],
                    "fields": f"{t['fields_count']}项" if t["fields_count"] else "-",
                    "error": t.get("error", ""),
                })

    return {"code": 0, "data": {"traces": traces}}
