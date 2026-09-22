"""SQLModel 数据模型（首批：用户 + 题库）。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """备考用户。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    nickname: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class Question(SQLModel, table=True):
    """题库题目：行测 / 申论 / 专业科目。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str = Field(index=True)  # 科目：行测 / 申论 / 专业
    content: str  # 题干
    answer: str = ""  # 参考答案
    analysis: str = ""  # 解析
    created_at: datetime = Field(default_factory=datetime.now)
