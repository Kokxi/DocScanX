"""DocScanX 入口 — 启动 Web 服务。"""
import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import init_config
from app.core.logging_config import get_system_logger, setup_logging


def create_app() -> FastAPI:
    """创建 FastAPI 应用。"""
    app = FastAPI(title="DocScanX", version="1.0.0", docs_url=None, redoc_url=None)

    # 注册 API 路由
    app.include_router(api_router)

    # 挂载前端静态文件
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def index():
        """返回首页。"""
        from fastapi.responses import FileResponse
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    return app


def main():
    """启动入口。"""
    # 1. 加载配置
    cfg = init_config()
    if cfg is None:
        print("[ERROR] 配置加载失败，无法启动")
        sys.exit(1)

    # 2. 初始化日志
    log_dir = getattr(cfg.path, "log_dir", "./logs")
    log_level = getattr(cfg.log, "level", "INFO")
    log_max_size = getattr(cfg.log, "max_size_mb", 10)

    setup_logging(log_dir=log_dir, max_size_mb=log_max_size, level=log_level)
    system_log = get_system_logger()

    # 3. 检查模型目录
    model_dir = getattr(cfg.path, "model_dir", "./models")
    if not os.path.isdir(model_dir) or not os.listdir(model_dir):
        system_log.warning(f"模型目录 {model_dir} 为空或不存在，请在 Phase 2 下载模型")

    # 4. 启动
    system_log.info(f"DocScanX 启动中... 访问 http://localhost:8080")
    uvicorn.run(create_app(), host="0.0.0.0", port=8080, log_level="info")


if __name__ == "__main__":
    main()
