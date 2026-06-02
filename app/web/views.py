"""Web 前端视图路由 — SPA 模式。"""
from fastapi import APIRouter, Request
from starlette.templating import _TemplateResponse

router = APIRouter()


def _render(request: Request, name: str, context: dict = None) -> _TemplateResponse:
    """用 Jinja2 环境渲染模板。"""
    ctx = context or {}
    ctx.setdefault("request", request)
    env = request.app.state.templates
    template = env.get_template(name)
    return _TemplateResponse(template, ctx, media_type="text/html")


@router.get("/")
async def spa(request: Request):
    return _render(request, "spa.html", {})


@router.get("/scan")
async def scan_page(request: Request):
    return _render(request, "spa.html", {})


@router.get("/subjects")
async def subjects_page(request: Request):
    return _render(request, "spa.html", {})


@router.get("/reports")
async def reports_page(request: Request):
    return _render(request, "spa.html", {})


@router.get("/settings")
async def settings_page(request: Request):
    return _render(request, "spa.html", {})


@router.get("/logs")
async def logs_page(request: Request):
    return _render(request, "spa.html", {})
