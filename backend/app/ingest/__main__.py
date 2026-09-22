"""真题入库命令行入口（python -m app.ingest）。

种子目录优先级：--seed > 环境变量 GKDP_SEED_DIR > config.yaml 的 ingest.seed_dir。
三者皆空则报错退出。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from app.config import config
from app.ingest.pipeline import format_report, run


def _resolve_seed(args_seed: str | None) -> Path | None:
    """按优先级解析种子目录。"""
    if args_seed:
        return Path(args_seed)
    env = os.environ.get("GKDP_SEED_DIR", "").strip()
    if env:
        return Path(env)
    cfg = config.get("ingest", {}).get("seed_dir", "").strip()
    if cfg:
        return Path(cfg)
    return None


def main() -> None:
    p = argparse.ArgumentParser(description="把真题资料目录灌入题库（幂等，可重建）")
    p.add_argument("--seed", default=None, help="真题种子目录（PDF/JSON 所在目录）")
    p.add_argument("--rebuild", action="store_true", help="先清空全部真题再全量重建")
    p.add_argument("--no-cache", action="store_true", help="不使用解析缓存，强制重新解析")
    args = p.parse_args()

    seed = _resolve_seed(args.seed)
    if seed is None:
        print("错误：未指定真题种子目录。")
        print("请通过 --seed 传入，例如：")
        print("  python -m app.ingest --seed <真题资料目录>")
        print("或用环境变量 GKDP_SEED_DIR，或在 config.yaml 的 ingest.seed_dir 配置。")
        sys.exit(1)

    if not seed.exists():
        print(f"错误：种子目录不存在：{seed}")
        sys.exit(1)

    report = run(seed, rebuild=args.rebuild, use_cache=not args.no_cache)
    print(format_report(report))


if __name__ == "__main__":
    main()
