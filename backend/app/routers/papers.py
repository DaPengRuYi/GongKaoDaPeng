"""查看历年真题接口：按科目 / 模块 / 年份 / 关键字浏览已入库真题。

年份从 source（卷名 + 页码）里用『\d{4}年』正则提取，无需改表结构。
"""
from __future__ import annotations

import json
import re
from typing import Optional

from fastapi import APIRouter, Query
from sqlmodel import Session, select

from app.database import engine
from app.models import Question

router = APIRouter(prefix="/api/papers", tags=["papers"])

_YEAR_PAT = re.compile(r"(\d{4})年")


def _year_of(q: Question) -> Optional[int]:
    m = _YEAR_PAT.search(q.source)
    return int(m.group(1)) if m else None


def _opts(q: Question) -> dict:
    try:
        return json.loads(q.options) if q.options else {}
    except Exception:
        return {}


@router.get("")
def list_papers(
    subject: Optional[str] = None,
    module: Optional[str] = None,
    year: Optional[int] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """分页浏览真题，并返回可用的筛选维度（科目/模块/年份）。"""
    stmt = (
        select(Question)
        .where(Question.is_real == True)
        .where(Question.question_type == "choice")
    )
    if subject:
        stmt = stmt.where(Question.subject == subject)
    if module:
        stmt = stmt.where(Question.module == module)
    if q:
        stmt = stmt.where(Question.content.contains(q))

    with Session(engine) as s:
        rows = s.exec(stmt).all()
        enriched = [
            {
                "id": r.id,
                "subject": r.subject,
                "module": r.module,
                "content": r.content,
                "options": _opts(r),
                "source": r.source,
                "year": _year_of(r),
                "is_real": r.is_real,
            }
            for r in rows
        ]

    if year is not None:
        enriched = [e for e in enriched if e["year"] == year]

    total = len(enriched)
    start = (page - 1) * page_size
    page_items = enriched[start : start + page_size]

    subjects = sorted({e["subject"] for e in enriched})
    modules = sorted({e["module"] for e in enriched if e["module"]})
    years = sorted({e["year"] for e in enriched if e["year"]}, reverse=True)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": page_items,
        "filters": {"subjects": subjects, "modules": modules, "years": years},
    }
