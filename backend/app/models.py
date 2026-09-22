"""SQLModel 数据模型（题库 + 答题记录 + 用户）。"""
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
    """题库题目：行测 / 职测 / 申论 / 综应 / 专业科目。

    字段设计对齐「一份录入，公考+事业编双轨通用」：
    - subject 容纳公考(行测/申论)与事业编(职测/综应)双轨；
    - module 区分五大模块（常识/言语/数量/判断/资料）；
    - options 以 JSON 字符串存（SQLite 无原生数组），解析侧统一拆 A/B/C/D；
    - source 记来源（卷次 + 页码），便于回溯与去重。
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str = Field(index=True)          # 行测 / 职测 / 申论 / 综应 / 专业
    module: str = ""                          # 常识判断 / 言语理解 / 数量关系 / 判断推理 / 资料分析 / 综合
    question_type: str = "choice"             # choice / judge / fill / subjective
    content: str                              # 题干（含题干引导语）
    options: str = ""                         # JSON 字符串 {"A":..,"B":..,"C":..,"D":..}
    answer: str = ""                          # 参考答案（选择题为字母，主观题为文本）
    analysis: str = ""                        # 解析
    difficulty: str = ""                      # easy / medium / hard
    source: str = ""                          # 来源：卷次 + 题号 + 页码
    is_real: bool = Field(default=True, index=True)  # 是否真题（true=真题，false=模拟题）
    created_at: datetime = Field(default_factory=datetime.now)


class QuestionAttempt(SQLModel, table=True):
    """答题记录：刷题闭环的判分基础。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(index=True, foreign_key="question.id")
    user_id: Optional[int] = Field(default=None, index=True, foreign_key="user.id")
    chosen: str = ""                          # 用户所选（选择题为字母）
    is_correct: Optional[bool] = None          # 客观题由代码判分；主观题暂留空，后续接入判分
    time_sec: int = 0                         # 单题用时（秒）
    error_tag: str = ""                        # 错因三桶：读题错 / 知识点错 / 计算错
    created_at: datetime = Field(default_factory=datetime.now)
