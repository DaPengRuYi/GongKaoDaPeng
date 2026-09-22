"""真题入库主入口（跨平台）。

    资料目录由用户通过 --seed 传入，不要硬编码本机路径。
用法：
    python scripts/ingest.py --seed <真题资料目录>
    python scripts/ingest.py --seed <真题资料目录> --rebuild
    python scripts/ingest.py --seed <真题资料目录> --no-cache
"""
from __future__ import annotations

import sys
from pathlib import Path

# 把 backend 加入模块搜索路径，这样无论从哪个目录运行都能 import app
BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ingest.__main__ import main

if __name__ == "__main__":
    main()
