"""SQLModel 数据库引擎与会话。"""
from __future__ import annotations

from sqlmodel import SQLModel, Session, create_engine

from app.config import config

_db_cfg = config.get("database", {})
DATABASE_URL = _db_cfg.get("url", "sqlite:///./gongkao.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=_connect_args)


def create_db_and_tables() -> None:
    """导入模型后建表（首次运行创建，已存在则跳过）。"""
    from app import models  # noqa: F401  确保模型注册到元数据

    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI 依赖：请求级数据库会话。"""
    with Session(engine) as session:
        yield session
