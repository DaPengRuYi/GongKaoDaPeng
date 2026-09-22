"""FastAPI 应用入口。"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.database import create_db_and_tables
from app.logging_conf import logger
from app.routers import home


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    app_cfg = config.get("app", {})
    logger.info("🚀 {} 启动完成 v{}", app_cfg.get("name"), app_cfg.get("version"))
    yield
    logger.info("👋 {} 已关闭", app_cfg.get("name"))


app_cfg = config.get("app", {})

app = FastAPI(
    title=app_cfg.get("name", "公考大鹏"),
    version=app_cfg.get("version", "0.1.0"),
    lifespan=lifespan,
)

_cors = config.get("cors", {})
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors.get("allow_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(home.router)


@app.get("/")
def root() -> dict:
    return {"msg": "公考大鹏 API 已启动", "docs": "/docs", "home": "/api/home"}
