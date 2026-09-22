"""真题 JSON → GongKaoDaPeng 数据库导入 + 判分 CLI（v0 最小闭环）。

只导入真实真题 JSON（由真题 PDF 解析而来的产物），
     绝不生成、绝不模拟、绝不补白。

两个子命令：
    python zhenti_cli.py import  <questions.json>   导入题库到 SQLite
    python zhenti_cli.py practice [--module 常识判断] [--n 20] [--seed 42]
                                                   随机抽 N 题 + 判分
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# GongKaoDaPeng 数据库路径
DB = Path(__file__).resolve().parent / "gongkao.db"
# 题库 JSON 目录（真题解析产物落这里）
QUESTIONS_DIR = Path(__file__).resolve().parent / "questions"


def ensure_schema(db: sqlite3.Connection) -> None:
    """建表（幂等）。"""
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS question (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            module TEXT DEFAULT '',
            question_type TEXT DEFAULT 'choice',
            content TEXT NOT NULL,
            options TEXT DEFAULT '',
            answer TEXT DEFAULT '',
            analysis TEXT DEFAULT '',
            difficulty TEXT DEFAULT '',
            source TEXT DEFAULT '',
            is_real INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(subject, module, source, content)
        );
        CREATE TABLE IF NOT EXISTS question_attempt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            chosen TEXT DEFAULT '',
            is_correct INTEGER,
            time_sec INTEGER DEFAULT 0,
            error_tag TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );
        """
    )
    db.commit()


def import_questions(db: sqlite3.Connection, json_path: Path) -> int:
    """把解析好的 JSON 导入 SQLite（幂等去重）。"""
    rows = json.loads(json_path.read_text(encoding="utf-8"))
    inserted = 0
    for r in rows:
        cur = db.execute(
            """
            INSERT OR IGNORE INTO question
              (subject, module, question_type, content, options, answer,
               analysis, difficulty, source, is_real)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                r["subject"],
                r.get("module", ""),
                r.get("question_type", "choice"),
                r["content"],
                r.get("options", ""),
                r.get("answer", ""),
                r.get("analysis", ""),
                r.get("difficulty", ""),
                r.get("source", ""),
                1 if r.get("is_real", True) else 0,
            ),
        )
        if cur.rowcount:
            inserted += 1
    db.commit()
    return inserted


def cmd_import(args) -> None:
    db = sqlite3.connect(DB)
    ensure_schema(db)
    n = import_questions(db, Path(args.json))
    total = db.execute("SELECT COUNT(*) FROM question").fetchone()[0]
    print(f"✅ 导入完成：新增 {n} 题，题库现共 {total} 题 → {DB}")
    db.close()


def cmd_practice(args) -> None:
    db = sqlite3.connect(DB)
    ensure_schema(db)
    # 选 20 道有选项的选择题
    where = ""
    params: list = []
    if args.module:
        where = "WHERE module = ? AND question_type = 'choice' AND options != ''"
        params.append(args.module)
    else:
        where = "WHERE question_type = 'choice' AND options != ''"
    rows = db.execute(f"SELECT * FROM question {where}", params).fetchall()
    if not rows:
        print(f"❌ 题库里没有满足条件的题（module={args.module or 'all'}）")
        db.close()
        return
    sample = random.sample(rows, min(args.n, len(rows)))
    print(f"\n===== 公考大鹏 · 刷题 {args.n} 题（{args.module or '全模块'}）=====")
    print("输入答案字母（A/B/C/D），回车提交；输入 q 退出\n")
    correct = 0
    for i, row in enumerate(sample, 1):
        qid, module, content, options, answer = (
            row[0],
            row[2],
            row[4],
            row[5],
            row[6],
        )
        opts = json.loads(options) if options else {}
        print(f"[{i}/{len(sample)}] ({module}) {content[:80]}")
        for k in "ABCD":
            if k in opts:
                print(f"  {k}. {opts[k][:50]}")
        chosen = input("你的答案: ").strip().upper()
        if chosen == "Q":
            print("\n👋 提前收工")
            break
        is_correct = None
        if answer:
            is_correct = chosen == answer.strip().upper()
            if is_correct:
                correct += 1
                mark = "✅ 答对"
            else:
                mark = f"❌ 答错（正确 {answer}）"
        else:
            mark = "（真题无答案，人工判）"
        db.execute(
            "INSERT INTO question_attempt (question_id, chosen, is_correct) VALUES (?, ?, ?)",
            (qid, chosen, is_correct),
        )
        print(f"  {mark}\n")
    db.commit()
    graded = sum(1 for r in sample if db.execute(
        "SELECT is_correct FROM question_attempt WHERE question_id=? AND is_correct IS NOT NULL",
        (r[0],),
    ).fetchone())
    print(f"===== 收工：做 {len(sample)} 题，代码判分 {graded} 题 =====")
    db.close()


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    p_imp = sub.add_parser("import", help="导入真题 JSON 到 SQLite")
    p_imp.add_argument("json", help="questions JSON 路径")
    p_imp.set_defaults(func=cmd_import)
    p_prac = sub.add_parser("practice", help="随机抽题 + 判分")
    p_prac.add_argument("--module", default="", help="模块名（常识判断/言语理解/数量关系/判断推理/资料分析）")
    p_prac.add_argument("--n", type=int, default=20, help="抽题数量")
    p_prac.add_argument("--seed", type=int, default=None, help="随机种子（可复现）")
    p_prac.set_defaults(func=cmd_practice)
    args = p.parse_args()
    if args.cmd == "import":
        cmd_import(args)
    elif args.cmd == "practice":
        cmd_practice(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
