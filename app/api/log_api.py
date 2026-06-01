"""日志查询 API 端点。"""
from fastapi import APIRouter, Query

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
