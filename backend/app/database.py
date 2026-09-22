"""SQLModel 数据库引擎与会话。"""
from __future__ import annotations

from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine

from app.config import BASE_DIR, config

_db_cfg = config.get("database", {})
_url = _db_cfg.get("url", "sqlite:///./gongkao.db")

# 相对路径的 SQLite 统一锚定到 backend 目录，避免随启动目录漂移。
# 否则从不同目录运行会导致 DB 文件位置不一致，破坏「资料在即可重建真题」的语义。
if _url.startswith("sqlite:///") and _url != "sqlite:///:memory:":
    _rel = _url[len("sqlite:///"):]
    if not Path(_rel).is_absolute():
        _url = "sqlite:///" + str((BASE_DIR / _rel).resolve()).replace("\\", "/")

_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}
engine = create_engine(_url, echo=False, connect_args=_connect_args)


def create_db_and_tables() -> None:
    """导入模型后建表（首次运行创建，已存在则跳过）。"""
    from app import models  # noqa: F401  确保模型注册到元数据

    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI 依赖：请求级数据库会话。"""
    with Session(engine) as session:
        yield session
