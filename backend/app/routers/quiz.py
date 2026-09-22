"""在线刷题接口：随机抽题 + 提交判分 + 错题本。

判分前提：真题答案由入库流水线的 backfill_answers 从『答案及解析』册回填。
若某题 answer 为空（暂无标准答案），submit 返回 graded=false，前端提示自行核对。
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, func, select

from app.database import engine
from app.models import Question, QuestionAttempt

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


def _opts(q: Question) -> dict:
    """options 字段是 JSON 字符串，解析成 dict 返回。"""
    try:
        return json.loads(q.options) if q.options else {}
    except Exception:
        return {}


def _to_item(q: Question) -> dict:
    return {
        "id": q.id,
        "subject": q.subject,
        "module": q.module,
        "content": q.content,
        "options": _opts(q),
    }


@router.get("/random")
def quiz_random(
    subject: Optional[str] = None,
    module: Optional[str] = None,
    n: int = Query(10, ge=1, le=50),
) -> dict:
    """随机抽取 n 道选择题；优先选已有答案的题，保证能自动判分。"""
    base = (
        select(Question)
        .where(Question.question_type == "choice")
        .where(Question.is_real == True)
    )
    if subject:
        base = base.where(Question.subject == subject)
    if module:
        base = base.where(Question.module == module)
    with Session(engine) as s:
        ans_count = s.exec(
            select(func.count())
            .select_from(base.where(Question.answer != "").subquery())
        ).one()
        use_ans = ans_count >= n
        pool = base.where(Question.answer != "") if use_ans else base
        rows = s.exec(pool.order_by(func.random()).limit(n)).all()
        items = [_to_item(q) for q in rows]
    return {"items": items, "graded_available": use_ans}


class QuizSubmitReq(BaseModel):
    question_id: int
    chosen: str
    user_id: Optional[int] = None
    time_sec: int = 0


@router.post("/submit")
def quiz_submit(req: QuizSubmitReq) -> dict:
    """提交作答并判分（客观题自动判；无标准答案则 graded=false）。"""
    with Session(engine) as s:
        q = s.get(Question, req.question_id)
        if not q:
            raise HTTPException(404, "题目不存在")
        correct = (q.answer or "").upper()
        graded = bool(correct)
        is_correct = req.chosen.upper() == correct if graded else None
        s.add(
            QuestionAttempt(
                question_id=q.id,
                user_id=req.user_id,
                chosen=req.chosen,
                is_correct=is_correct,
                time_sec=req.time_sec,
            )
        )
        s.commit()
        return {
            "question_id": q.id,
            "chosen": req.chosen,
            "correct": q.answer or "",
            "is_correct": is_correct,
            "analysis": q.analysis or "",
            "graded": graded,
        }


@router.get("/wrong")
def quiz_wrong(
    user_id: Optional[int] = None,
    subject: Optional[str] = None,
    module: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    """错题本：取答错的记录（可再按科目/模块过滤）。"""
    stmt = (
        select(QuestionAttempt, Question)
        .join(Question, QuestionAttempt.question_id == Question.id)
        .where(QuestionAttempt.is_correct == False)
    )
    if user_id is not None:
        stmt = stmt.where(QuestionAttempt.user_id == user_id)
    if subject:
        stmt = stmt.where(Question.subject == subject)
    if module:
        stmt = stmt.where(Question.module == module)
    with Session(engine) as s:
        rows = s.exec(
            stmt.order_by(QuestionAttempt.created_at.desc()).limit(limit)
        ).all()
        items = [
            {
                "id": q.id,
                "subject": q.subject,
                "module": q.module,
                "content": q.content,
                "options": _opts(q),
                "chosen": a.chosen,
                "correct": q.answer,
                "analysis": q.analysis or "",
            }
            for a, q in rows
        ]
    return {"items": items}
