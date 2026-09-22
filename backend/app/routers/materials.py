"""学习资料接口：浏览『资料』种子目录的辅导资料 / 真题册，并流式返回 PDF。

目录树从配置或环境变量 GKDP_SEED_DIR 指向的种子目录读取（绝不回写）。
路径做了越界防护：只允许访问种子目录以内的文件。
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.config import config
from app.ingest.classify import JUNK_KEYWORDS
from app.ingest.parser import win_long_path

router = APIRouter(prefix="/api/materials", tags=["materials"])


def _seed_dir() -> Path:
    d = os.environ.get("GKDP_SEED_DIR") or config.get("ingest", {}).get("seed_dir", "")
    if not d or not Path(d).exists():
        raise HTTPException(
            500,
            "未配置资料目录：请设置环境变量 GKDP_SEED_DIR 或 config.ingest.seed_dir",
        )
    return Path(d)


def _is_junk(name: str) -> bool:
    return any(kw in name for kw in JUNK_KEYWORDS)


@router.get("")
def list_materials(path: str = "", q: str = "") -> dict:
    """列出某目录下的子目录与 PDF 文件（跳过辅导资料目录，文件名关键字过滤）。"""
    root = _seed_dir()
    cur = (root / path) if path else root
    if not str(cur.resolve()).startswith(str(root.resolve())):
        raise HTTPException(400, "非法路径")
    entries = []
    try:
        for p in sorted(cur.iterdir(), key=lambda x: (x.is_file(), x.name)):
            if p.is_dir():
                if _is_junk(p.name):
                    continue
                entries.append(
                    {
                        "name": p.name,
                        "type": "dir",
                        "key": str(p.relative_to(root)),
                        "size": None,
                    }
                )
            elif p.suffix.lower() == ".pdf":
                if q and q not in p.name:
                    continue
                try:
                    size = p.stat().st_size
                except Exception:
                    size = None
                entries.append(
                    {
                        "name": p.name,
                        "type": "file",
                        "key": str(p.relative_to(root)),
                        "size": size,
                    }
                )
    except Exception:
        pass
    return {"root": root.name, "path": path, "entries": entries}


@router.get("/file")
def get_material_file(key: str = Query(...)) -> FileResponse:
    """流式返回某个 PDF（inline 打开，便于浏览器直接预览）。"""
    root = _seed_dir()
    target = (root / key).resolve()
    if str(target).startswith(str(root.resolve())) is False or not target.exists():
        raise HTTPException(404, "文件不存在")
    if target.suffix.lower() != ".pdf":
        raise HTTPException(400, "仅支持 PDF")
    # 用 \\?\ 长路径前缀规避 Windows MAX_PATH 限制
    return FileResponse(
        win_long_path(target),
        media_type="application/pdf",
        filename=target.name,
    )
