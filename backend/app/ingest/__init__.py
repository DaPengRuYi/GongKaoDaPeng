"""真题入库流水线包：分类、解析、幂等入库。

对外暴露 run()，方便脚本与命令行直接调用：
    from app.ingest import run
"""
from app.ingest.pipeline import run

__all__ = ["run"]
