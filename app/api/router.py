"""API 路由注册。"""
from fastapi import APIRouter

from app.api.config_api import router as config_router
from app.api.log_api import router as log_router
from app.api.scan_api import router as scan_router
from app.api.report_api import router as report_router
from app.api.subject_api import router as subject_router
from app.api.remote_api import router as remote_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(config_router, tags=["config"])
api_router.include_router(log_router, tags=["logs"])
api_router.include_router(scan_router, tags=["scan"])
api_router.include_router(report_router, tags=["reports"])
api_router.include_router(subject_router, tags=["subjects"])
api_router.include_router(remote_router, tags=["remote"])
