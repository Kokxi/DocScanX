"""数据主体查询 API。"""
import json
import os

from fastapi import APIRouter, Query

from app.core import config as config_module
from app.engine.report import list_reports
from app.engine.risk import add_risk_to_person_dict

router = APIRouter()


def _output_dir():
    cfg = config_module.config
    return getattr(cfg.path, "output_dir", "./output") if cfg else "./output"


def _load_all_persons(output_dir: str) -> list:
    """从所有报告中加载人员数据。"""
    persons = []
    for r in list_reports(output_dir):
        json_path = os.path.join(output_dir, r["id"], "report.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for p in data.get("persons", []):
                p["report_id"] = r["id"]
                if "risk" not in p:
                    add_risk_to_person_dict(p)
                persons.append(p)
    return persons


@router.get("/subjects")
async def api_list_subjects(search: str = Query(default=""), page: int = Query(default=1),
                            per_page: int = Query(default=50)):
    """列出/搜索数据主体。"""
    persons = _load_all_persons(_output_dir())

    if search:
        q = search.lower()
        persons = [p for p in persons
                   if q in (p.get("name") or "").lower()
                   or q in (p.get("id_card") or "")
                   or q in (p.get("phone") or "")]

    total = len(persons)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "code": 0,
        "data": {
            "persons": persons[start:end],
            "total": total,
            "page": page,
            "per_page": per_page,
        },
    }
