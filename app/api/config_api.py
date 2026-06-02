"""配置相关 API 端点。"""
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from app.core import config as config_module
from app.core.config import (
    _namespace_to_dict,
    _deep_merge,
    load_default_config,
    save_config,
)
from app.core.logging_config import get_audit_logger, get_system_logger

router = APIRouter()


@router.get("/health")
async def health():
    """健康检查 + 模型就绪状态。"""
    cfg = config_module.config
    model_dir = getattr(cfg.path, "model_dir", "./models") if cfg else "./models"
    models_ready = bool(os.path.isdir(model_dir) and os.listdir(model_dir))
    return {
        "code": 0,
        "data": {"status": "ok", "models_ready": models_ready, "timestamp": datetime.now().isoformat()},
        "message": "ok",
    }


@router.get("/config")
async def get_config():
    """获取当前完整配置。"""
    return {
        "code": 0,
        "data": _namespace_to_dict(config_module.config) if config_module.config else {},
        "message": "ok",
    }


@router.put("/config")
async def update_config(request: Request):
    """更新配置并持久化到 config.yaml。"""
    body = await request.json()
    if not body or not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="请求体必须为 JSON 对象")

    try:
        _deep_merge(config_module.config, body)
        save_config(config_module.config)
        get_audit_logger().info(f"配置变更: {list(body.keys())}")
        return {"code": 0, "data": _namespace_to_dict(config_module.config), "message": "配置已保存"}
    except Exception as e:
        get_system_logger().error(f"配置更新失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config/defaults")
async def get_default_config():
    """获取出厂默认配置。"""
    try:
        defaults = load_default_config()
        return {"code": 0, "data": _namespace_to_dict(defaults), "message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
