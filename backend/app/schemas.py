"""首页响应模型（Pydantic / SQLModel Schema）。"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel


class FeatureItem(BaseModel):
    icon: str
    title: str
    desc: str


class HomeResponse(BaseModel):
    app_name: str
    version: str
    title: str
    subtitle: str
    slogan: str
    features: List[FeatureItem]
    cta_text: str
    cta_url: str
