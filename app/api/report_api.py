"""报告管理 API。"""
import json
import logging
import os

from fastapi import APIRouter
from fastapi.responses import Response

from app.core import config as config_module
from app.engine.report import list_reports

router = APIRouter()
audit = logging.getLogger("audit")


def _output_dir():
    cfg = config_module.config
    return getattr(cfg.path, "output_dir", "./output") if cfg else "./output"


@router.get("/reports")
async def api_list_reports():
    """列出所有报告。"""
    reports = list_reports(_output_dir())
    return {"code": 0, "data": {"reports": reports}}


@router.get("/reports/{report_id}")
async def api_get_report(report_id: str):
    """获取单个报告详情。"""
    json_path = os.path.join(_output_dir(), report_id, "report.json")
    if not os.path.exists(json_path):
        return {"code": 1, "message": "报告不存在"}
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"code": 0, "data": data}


@router.get("/reports/{report_id}/export")
async def api_export_report(report_id: str, format: str = "json"):
    """导出报告，支持 json/xlsx/csv/html。"""
    audit.info(f"报告导出: {report_id} (格式: {format})")
    report_dir = os.path.join(_output_dir(), report_id)

    if format == "json":
        path = os.path.join(report_dir, "report.json")
        if not os.path.exists(path):
            return {"code": 1, "message": "报告不存在"}
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content, media_type="application/json",
                        headers={"Content-Disposition": f"attachment; filename={report_id}.json"})

    elif format == "xlsx":
        path = os.path.join(report_dir, "report.xlsx")
        if not os.path.exists(path):
            return {"code": 1, "message": "Excel 报告不存在"}
        with open(path, "rb") as f:
            content = f.read()
        return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f"attachment; filename={report_id}.xlsx"})

    elif format == "csv":
        path = os.path.join(report_dir, "report.csv")
        if not os.path.exists(path):
            return {"code": 1, "message": "CSV 报告不存在"}
        with open(path, "r", encoding="utf-8-sig") as f:
            content = f.read()
        return Response(content, media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={report_id}.csv"})

    elif format == "html":
        path = os.path.join(report_dir, "report.html")
        if not os.path.exists(path):
            return {"code": 1, "message": "HTML 报告不存在"}
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content, media_type="text/html")

    else:
        return {"code": 1, "message": f"不支持的格式: {format}"}
