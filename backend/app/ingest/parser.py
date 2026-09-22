"""把真题 PDF 解析成结构化题目（可导入版）。

逻辑移植自用户已有的 parse_zhenti.py，保持原有的切题算法不变，
只做了「可导入化」与「不崩溃」两处增强：

- subject 由参数传入，不再硬编码为「职测」；
- 用 try/except 包住读取与切题，损坏的 PDF 不会让整条流水线中断，
  并返回状态标记（ok / no_text / error）便于上层统计。
"""
from __future__ import annotations

import json
import os
import re
import sys
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

# 五大模块标题正则（与真题卷一致）
MODULE_PATTERNS = [
    (r"一、常识判断", "常识判断"),
    (r"二、言语理解与表达", "言语理解"),
    (r"三、数量关系", "数量关系"),
    (r"四、判断推理", "判断推理"),
    (r"五、资料分析", "资料分析"),
]


def win_long_path(p: str | Path) -> str:
    r"""把路径转成 Windows 长路径安全形式（\\?\ 前缀），避免 >260 字符读失败。

    资料目录里有些真题 PDF 嵌套很深、文件名很长，普通 open() 会报
    FileNotFoundError（WinError 206）。补上 \\?\ 前缀后用绝对路径反斜杠形式打开，
    既不影响读取，也不会让 PdfReader 在内部再次踩 MAX_PATH 限制。
    非 Windows / 已是前缀的路径原样返回。
    """
    s = os.fspath(p)
    if os.name == "nt" and not s.startswith("\\\\?\\"):
        s = os.path.abspath(s).replace("/", "\\")
        if s.startswith("\\\\"):  # UNC 共享路径
            s = "\\\\?\\UNC" + s[1:]
        else:
            s = "\\\\?\\" + s
    return s


def _extract_full_text(pdf_path: str | Path) -> str:
    r"""逐页抽取全文，并在每页前插入 @@PAGE n@@ 标记，便于回溯页码。

    整文件读入 BytesIO 再交给 PdfReader，规避 pypdf 关闭我传入的文件句柄后
    再 seek 导致的 "seek of closed file"；同时用 \\?\ 长路径前缀规避 MAX_PATH 限制。
    """
    with open(win_long_path(pdf_path), "rb") as fh:
        data = fh.read()
    reader = PdfReader(BytesIO(data))
    parts = []
    for i, page in enumerate(reader.pages):
        parts.append(f"\n@@PAGE {i + 1}@@\n")
        parts.append(page.extract_text() or "")
    return "".join(parts)


def _split_options(block: str) -> tuple[str, dict[str, str]]:
    """把一道题的原文块拆成（题干, {A:..,B:..,C:..,D:..}）。"""
    option_pat = re.compile(r"([A-D])、\s*([^\n]*)", re.MULTILINE)
    matches = list(option_pat.finditer(block))
    if len(matches) < 2:
        return block.strip(), {}
    stem = block[: matches[0].start()].strip()
    opts = {}
    for idx, m in enumerate(matches):
        key = m.group(1)
        val = m.group(2).strip()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(block)
        seg = block[m.end():end]
        opts[key] = (val + seg).strip()
    return stem, opts


def _parse_questions(text: str, pdf_path: str | Path, subject: str) -> list[dict]:
    """把整卷全文切成一道道选择题，返回可直接入库的字段字典列表。

    算法与用户版 parse_zhenti 保持一致：先按模块标题切段，
    再在每段内按题号严格递增切题，跳过引导语和子标题里的干扰数字。
    """
    questions: list[dict] = []
    stem = Path(pdf_path)

    # 第一步：按模块标题切全文为若干段
    mod_starts: list[tuple[str, int]] = []
    for pat, name in MODULE_PATTERNS:
        m = re.search(pat, text)
        if m:
            mod_starts.append((name, m.start()))
    mod_starts.sort(key=lambda x: x[1])
    if not mod_starts:
        mod_starts = [("", 0)]

    segments: list[tuple[str, str]] = []
    for i, (name, start) in enumerate(mod_starts):
        end = mod_starts[i + 1][1] if i + 1 < len(mod_starts) else len(text)
        segments.append((name, text[start:end]))

    # 第二步：每段内按题号递增切题，跳过干扰数字
    num_pat = re.compile(r"^(\d{1,3})\s*$", re.MULTILINE)
    for mod_name, seg in segments:
        positions = [(int(m.group(1)), m.start()) for m in num_pat.finditer(seg)]
        if not positions:
            continue
        # 跳过模块标题引导语里的数字（形如「一、常识判断。根据…答案。」）
        guide_len = 0
        gm = re.match(r"^[一二三四五六七八九十]+、[^。\n]*[。．]\n?", seg)
        if gm:
            guide_len = gm.end()
        filtered: list[tuple[int, int]] = []
        last_num = 0
        for num, pos in positions:
            if pos < guide_len:
                continue
            if num == last_num + 1 or (last_num == 0 and num <= 100):
                if last_num == 0:
                    last_num = num - 1
                if num == last_num + 1:
                    filtered.append((num, pos))
                    last_num = num
                # 若严格断链（干扰数字），重新锚定
                else:
                    last_num = num - 1
                    filtered.append((num, pos))
                    last_num = num
        if not filtered:
            continue
        for i, (num, start) in enumerate(filtered):
            end = filtered[i + 1][1] if i + 1 < len(filtered) else len(seg)
            block = seg[start:end]
            q_stem, opts = _split_options(block)
            # 去题号 + 模块引导语 + 卷头
            q_stem = re.sub(r"^\s*\d{1,3}\s*", "", q_stem).strip()
            q_stem = re.sub(r"^[一二三四五六七八九十]+、[^。]*。\s*", "", q_stem).strip()
            q_stem = re.sub(r"^\d{4}年.*?笔试真题\s*", "", q_stem).strip()
            q_stem = re.sub(r"^[（(]\d+[)）]\s*", "", q_stem).strip()  # 子标题（一）（二）
            # 反查页码
            prefix = seg[:start]
            mpage = re.findall(
                r"@@PAGE (\d+)@@",
                text[: text.find(seg) + len(prefix)] if seg in text else "",
            )
            pg = int(mpage[-1]) if mpage else 1
            # 只收录选项数 >= 2 的选择题
            if len(opts) < 2:
                continue
            questions.append(
                {
                    "subject": subject,
                    "module": mod_name,
                    "question_type": "choice",
                    "content": q_stem,
                    "options": json.dumps(opts, ensure_ascii=False),
                    "answer": "",
                    "analysis": "",
                    "difficulty": "",
                    "source": f"{stem.stem}#Q{num}@p{pg}",
                    "is_real": True,
                }
            )
    return questions


def parse_pdf(pdf_path: str | Path, subject: str) -> tuple[list[dict], str]:
    """解析单个真题 PDF，返回（题目列表, 状态）。

    状态取值：
    - "ok"：正常解析出题目
    - "no_text"：抽取出的全文过短，可能是扫描件或空白卷
    - "error"：读取 / 切题过程抛异常

    损坏的 PDF 会返回空列表而不是抛错，保证整条流水线不被单个坏文件打断。
    """
    try:
        text = _extract_full_text(pdf_path)
    except Exception as exc:  # 读取损坏的 PDF 不应让流水线中断
        print(f"⚠️ 解析失败（{pdf_path}）：{exc}", file=sys.stderr)
        return [], "error"
    if len(text) < 200:
        return [], "no_text"
    try:
        questions = _parse_questions(text, pdf_path, subject)
    except Exception as exc:
        print(f"⚠️ 切题失败（{pdf_path}）：{exc}", file=sys.stderr)
        return [], "error"
    return questions, "ok"
