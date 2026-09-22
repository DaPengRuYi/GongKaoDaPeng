"""loguru 日志配置：同时输出控制台与文件（按配置滚动/保留）。"""
from __future__ import annotations

from pathlib import Path

from loguru import logger

from app.config import config

_log_cfg = config.get("logging", {})
_level = _log_cfg.get("level", "INFO")

# 控制台 sink（带颜色）
logger.remove()
logger.add(
    sink=lambda msg: print(msg, end=""),
    level=_level,
    colorize=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
)

# 文件 sink（无颜色，滚动 + 保留）
_log_file = _log_cfg.get("file")
if _log_file:
    _log_path = Path(_log_file)
    _log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        sink=str(_log_path),
        level=_level,
        rotation=_log_cfg.get("rotation", "10 MB"),
        retention=_log_cfg.get("retention", "7 days"),
        encoding="utf-8",
        enqueue=True,
        colorize=False,
    )

__all__ = ["logger"]
