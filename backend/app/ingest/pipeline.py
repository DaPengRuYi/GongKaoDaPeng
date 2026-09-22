"""真题入库流水线：扫描种子目录、分类、解析、幂等入库。

设计要点：
- 种子目录（资料）是只读输入，解析缓存落在项目内的 backend/.cache/parsed，
  绝不回写资料目录；
- 去重靠（subject, module, source, content）唯一键，权威手段是 CREATE UNIQUE INDEX；
- run() 幂等：重复运行不会翻倍；rebuild=True 时先清空真题行，再全量重建，
  从而保证「只要资料目录还在，就能从零重建真题库」。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from sqlmodel import Session, delete, func, select, text

from app.database import engine
from app.ingest.classify import classify, subject_of
from app.ingest.parser import parse_pdf, win_long_path, _extract_full_text
from app.models import Question, SQLModel  # 触发模型注册到元数据

# 缓存落在项目内（backend/.cache/parsed），绝不回写只读的种子（资料）目录
# __file__ 位于 backend/app/ingest/pipeline.py，上溯三级到 backend 目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
_CACHE_ROOT = BASE_DIR / ".cache" / "parsed"

# Question 表入库时只取这些字段，过滤掉 JSON 里可能多余/拼错的键
_Q_FIELDS = [
    "subject", "module", "question_type", "content", "options",
    "answer", "analysis", "difficulty", "source", "is_real",
]


def ensure_dedup_index() -> None:
    """建立唯一索引（subject, module, source, content）作为权威去重手段。

    无论 models 是否带约束，这个索引都能在「现有表」上生效
    （create_all 对老表不会自动加约束），避免重复导入把真题翻倍。
    """
    with Session(engine) as s:
        s.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_question_seed "
                "ON question(subject, module, source, content)"
            )
        )
        s.commit()


def discover_pdfs(seed_dir: Path) -> list[Path]:
    """递归找出种子目录下所有 PDF。"""
    return sorted(seed_dir.rglob("*.pdf"))


def _safe_name(pdf: Path) -> str:
    """缓存文件名用 PDF 绝对路径的定长哈希。

    不要拼相对路径进文件名：资料目录里有些真题 PDF 嵌套很深、文件名很长，
    拼出来会超过 Windows 的 MAX_PATH(260)，写缓存会报 FileNotFoundError。
    哈希定长，且按绝对路径唯一（不同种子目录里的同名文件不会冲突）。
    用 win_long_path 取绝对路径形式做哈希，深路径也不会在解析时先踩坑。
    """
    return hashlib.sha1(win_long_path(pdf).encode("utf-8")).hexdigest()[:20]


def _cache_path(seed_dir: Path, pdf: Path) -> Path:
    """解析缓存落点：backend/.cache/parsed/<定长哈希>.json。"""
    return _CACHE_ROOT / (_safe_name(pdf) + ".json")


def _load_cache(cache_file: Path, pdf: Path) -> tuple[list[dict], str] | None:
    """读取缓存；若缓存缺失或 PDF 已变更（mtime 变了）则返回 None。"""
    if not cache_file.exists():
        return None
    try:
        cache = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return None
    try:
        mtime = pdf.stat().st_mtime
    except Exception:
        return None
    if cache.get("mtime") != mtime:
        return None
    return cache.get("questions", []), cache.get("status", "ok")


def _write_cache(cache_file: Path, questions: list[dict], status: str, pdf: Path) -> None:
    """把解析结果写入项目内缓存（记录 mtime 以便失效判断）。"""
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {"mtime": Path(win_long_path(pdf)).stat().st_mtime, "status": status, "questions": questions}
    cache_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _normalize_row(raw: dict) -> dict:
    """从任意真题 JSON 的一行取规范字段，缺省用安全默认值。"""
    row = {f: raw.get(f, "") for f in _Q_FIELDS}
    row["is_real"] = bool(raw.get("is_real", True))
    if row["question_type"] not in ("choice", "judge", "fill", "subjective"):
        row["question_type"] = "choice"
    return row


def run(seed_dir: Path, rebuild: bool = False, use_cache: bool = True) -> dict:
    """执行一次入库，返回覆盖率报告字典。

    幂等：重复运行不会翻倍。rebuild=True 时先清空所有真题行，再全量重建。
    """
    seed_dir = Path(seed_dir)
    # 确保表与唯一索引都存在（无论表是新建还是已有）
    SQLModel.metadata.create_all(engine)
    ensure_dedup_index()

    if rebuild:
        # 清掉全部真题行，准备全量重建
        with Session(engine) as s:
            s.exec(delete(Question).where(Question.is_real == True))
            s.commit()

    total_pdfs = junk = unknown = subjective_skipped = choice_parsed = 0
    unparsed = json_loaded = choice_empty = 0
    collected: list[dict] = []

    # 1) PDF：分类 → 解析（命中缓存则跳过解析）
    for pdf in discover_pdfs(seed_dir):
        total_pdfs += 1
        kind = classify(pdf)
        if kind == "junk":
            junk += 1
            continue
        if kind == "unknown":
            unknown += 1
            continue
        if kind == "subjective":
            subjective_skipped += 1
            continue
        # kind == "choice"
        choice_parsed += 1
        questions: list[dict] = []
        status = "ok"
        if use_cache:
            cached = _load_cache(_cache_path(seed_dir, pdf), pdf)
            if cached is not None:
                questions, status = cached
        if questions == [] and status == "ok":
            # 没命中缓存才真正解析
            questions, status = parse_pdf(pdf, subject_of(pdf))
            if use_cache:
                _write_cache(_cache_path(seed_dir, pdf), questions, status, pdf)
        if status in ("no_text", "error"):
            unparsed += 1
            continue
        if status == "ok" and not questions:
            # 选择题卷但没切出题目（如大纲/金句/纯答案册），不入库也不算异常
            choice_empty += 1
            continue
        collected.extend(_normalize_row(q) for q in questions)

    # 2) 一层已有的真题 JSON（如 questions_zhice_A_202503.json）
    for jf in sorted(seed_dir.glob("*.json")):
        try:
            rows = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(rows, list):
            continue
        json_loaded += 1
        collected.extend(_normalize_row(r) for r in rows if isinstance(r, dict))

    # 3) 幂等 upsert：内存去重 + 库内已存在去重，双保险
    inserted = skipped = 0
    seen: set[tuple] = set()
    with Session(engine) as session:
        existing = set()
        for r in session.exec(
            select(Question.subject, Question.module, Question.source, Question.content)
        ).all():
            existing.add((r[0], r[1], r[2], r[3]))
        for q in collected:
            key = (q["subject"], q["module"], q["source"], q["content"])
            if key in seen or key in existing:
                skipped += 1
                continue
            seen.add(key)
            session.add(Question(**q))
            inserted += 1
            if inserted % 1000 == 0:
                session.commit()
        session.commit()
        total_db_real = session.exec(
            select(func.count()).select_from(Question).where(Question.is_real == True)
        ).one()

    # 4) 答案回填：把答案册里的标准答案补回真题，使在线刷题能自动判分
    backfill = backfill_answers(seed_dir)

    return {
        "total_pdfs": total_pdfs,
        "junk": junk,
        "unknown": unknown,
        "subjective_skipped": subjective_skipped,
        "choice_parsed": choice_parsed,
        "choice_empty": choice_empty,
        "unparsed": unparsed,
        "json_loaded": json_loaded,
        "collected": len(collected),
        "inserted": inserted,
        "skipped": skipped,
        "total_db_real": total_db_real,
        "answers_updated": backfill.get("answers_updated", 0),
    }


# ---------------------------------------------------------------------------
# 答案回填：真题卷多数只存了题干，标准答案在并列的「答案及解析」册里。
# 这一步把答案按「卷名 + 题号」回填，是在线刷题能自动判分的前提。
# ---------------------------------------------------------------------------

def _find_answer_pdfs(seed_dir: Path) -> list[Path]:
    """找出答案册 PDF：文件名含『答案/解析』且不是辅导资料(junk)。"""
    out: list[Path] = []
    for pdf in discover_pdfs(seed_dir):
        name = pdf.name
        if ("答案" in name or "解析" in name) and classify(pdf) != "junk":
            out.append(pdf)
    return out


def _extract_answers(text: str) -> dict[int, str]:
    """从答案册正文抽 (题号 -> 选项字母)。兼容 '1. A' / '1、A' / '1．A' / '1【A】'。"""
    ans: dict[int, str] = {}
    for m in re.finditer(r"(?m)^(\d{1,3})[\.、．\s]+([A-Da-d])", text):
        ans[int(m.group(1))] = m.group(2).upper()
    if not ans:
        for m in re.finditer(r"(\d{1,3})\s*[【\[]\s*([A-Da-d])\s*[\]】]", text):
            ans[int(m.group(1))] = m.group(2).upper()
    return ans


def backfill_answers(seed_dir: Path) -> dict:
    """把答案册标准答案按『卷名 + 题号』回填到已入库真题。

    匹配规则：真题 source 形如 '<卷名>#Q<num>@p<pg>'，答案册文件名通常 =
    '<卷名>答案及解析(1)'，即卷名是答案册名的前缀；对每本答案册抽 (题号->字母)，
    再给该卷下对应题号回填 answer。只填当前为空的，幂等可重复跑。
    """
    seed_dir = Path(seed_dir)
    # 建立 卷名 -> [(qid, num)]
    by_stem: dict[str, list[tuple[int, int]]] = {}
    with Session(engine) as s0:
        for qid, src in s0.exec(
            select(Question.id, Question.source).where(Question.is_real == True)
        ).all():
            if "#Q" not in src:
                continue
            stem = src.split("#Q", 1)[0]
            m = re.search(r"#Q(\d+)@", src)
            num = int(m.group(1)) if m else 0
            by_stem.setdefault(stem, []).append((qid, num))

    updated = 0
    with Session(engine) as s:
        for pdf in _find_answer_pdfs(seed_dir):
            astem = pdf.stem
            matched = [st for st in by_stem if st and st in astem]
            if not matched:
                continue
            try:
                text = _extract_full_text(pdf)
            except Exception:
                continue
            ans = _extract_answers(text)
            if not ans:
                continue
            for st in matched:
                for qid, num in by_stem[st]:
                    if num in ans:
                        q = s.get(Question, qid)
                        if q and not q.answer:
                            q.answer = ans[num]
                            updated += 1
        s.commit()
    return {"answer_pdfs": len(_find_answer_pdfs(seed_dir)), "answers_updated": updated}


def format_report(report: dict) -> str:
    """把覆盖率报告渲染成中文文本，供命令行直接打印。"""
    lines = [
        "===== 公考大鹏 · 真题入库报告 =====",
        f"扫描 PDF 总数：{report['total_pdfs']}",
        f"  跳过（垃圾资料）：{report['junk']}",
        f"  未识别（unknown，可能是漏网真题）：{report['unknown']}",
        f"  跳过（申论/综应主观题）：{report['subjective_skipped']}",
        f"  选择题卷（已解析）：{report['choice_parsed']}",
        f"  选择题卷（切出 0 题）：{report['choice_empty']}",
        f"  解析失败/无文本：{report['unparsed']}",
        f"  直接加载 JSON 文件数：{report['json_loaded']}",
        f"  收集题目总数：{report['collected']}",
        f"  本次新增入库：{report['inserted']}",
        f"  幂等跳过（已存在）：{report['skipped']}",
        f"  当前真题库总量：{report['total_db_real']}",
        f"  标准答案回填：{report.get('answers_updated', 0)} 题",
        "",
        "提示：只要资料目录还在，就能用下面命令从零重建真题库：",
        "  python scripts/ingest.py --seed <资料目录> --rebuild",
        "  （等价模块入口：python -m app.ingest --seed <资料目录> --rebuild）",
    ]
    return "\n".join(lines)
