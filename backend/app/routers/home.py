"""首页相关接口。"""
from __future__ import annotations

from fastapi import APIRouter

from app.config import config
from app.schemas import FeatureItem, HomeResponse

router = APIRouter(tags=["home"])


@router.get("/api/home", response_model=HomeResponse)
def get_home() -> HomeResponse:
    """返回首页展示所需的全部数据，前端纯展示、不写死文案。"""
    app_cfg = config.get("app", {})
    return HomeResponse(
        app_name=app_cfg.get("name", "公考大鹏"),
        version=app_cfg.get("version", "0.1.0"),
        title="公考大鹏",
        subtitle="程序员公考 · 用工程能力降维打击",
        slogan="别人用笔和脑子磨，我们用代码把学习与面试效率拉满。",
        features=[
            FeatureItem(icon="📚", title="智能刷题", desc="随机抽题 + 自动判分，错题本与间隔复习一体化。"),
            FeatureItem(icon="🎯", title="岗位匹配", desc="按学历 / 专业 / 年龄结构化筛选，算出真正能报的岗。"),
            FeatureItem(icon="🎤", title="面试训练", desc="录音转写 + AI 点评，表达力可量化提升。"),
            FeatureItem(icon="🕸️", title="知识图谱", desc="专业科目知识图谱，强弱项一眼看穿。"),
        ],
        cta_text="开始备考",
        cta_url="/api/home",
    )
