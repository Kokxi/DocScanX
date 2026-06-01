"""API 路由注册。"""
from fastapi import APIRouter

from app.api.config_api import router as config_router
from app.api.log_api import router as log_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(config_router, tags=["config"])
api_router.include_router(log_router, tags=["logs"])
