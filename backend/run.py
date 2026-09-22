"""开发启动入口：python run.py"""
from __future__ import annotations

import uvicorn

from app.config import config

app_cfg = config.get("app", {})

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=app_cfg.get("host", "0.0.0.0"),
        port=app_cfg.get("port", 8000),
        reload=app_cfg.get("debug", False),
    )
