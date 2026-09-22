"""配置加载：从 config.yaml 读取并缓存为字典。"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

# backend/ 目录（config.yaml 与 run.py 所在层）
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"


@lru_cache(maxsize=1)
def get_config() -> dict:
    """读取 YAML 配置，仅加载一次。"""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"找不到配置文件: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 全局配置对象，模块直接 import 使用
config: dict = get_config()
