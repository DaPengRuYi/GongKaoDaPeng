"""按路径特征给真题 PDF 分类，决定要不要入库。

分类只看路径（目录名 + 文件名），不读 PDF 内容，速度很快，
便于在 3500+ 个文件里快速筛出真正需要解析的真题卷。
"""
from __future__ import annotations

from pathlib import Path

# 干扰文件关键词：辅导笔记、口诀、模拟卷、预测、营销物料等都不是真题卷，直接跳过
JUNK_KEYWORDS = [
    "笔记", "秒杀", "口诀", "思维导图", "规范词", "三色", "万能", "热词",
    "图推", "成语", "合集", "技巧", "公式", "考点", "预测", "模拟", "冲刺",
    "干货", "模板", "复盘", "晨读", "打卡", "计划", "易错", "高频", "速记",
    "押题", "赠送", "参考", "不推荐", "资料大全",
]

# 命中其一即判定为选择题真题卷
CHOICE_HINTS = ("职测", "行测", "联考", "国考", "省考", "真题")


def classify(path: Path) -> str:
    """把 PDF 归入四类之一。

    - "junk"：辅导资料 / 营销物料，不是真题卷
    - "subjective"：申论 / 综应主观题，本次不入库（只计数）
    - "choice"：职测 / 行测等选择题真题，需要解析入库
    - "unknown"：认不出来，提示用户可能是漏网的真题

    判定顺序：先扫垃圾词，再看主观题，最后看选择题关键词。
    """
    p = Path(path)
    # 路径的每一段（含各级目录名和文件名）命中干扰词就判为垃圾
    for part in p.parts:
        if any(kw in part for kw in JUNK_KEYWORDS):
            return "junk"
    name = p.name
    if "综应" in name or "申论" in name or "综合应用" in name:
        return "subjective"
    if any(k in name for k in CHOICE_HINTS):
        return "choice"
    return "unknown"


def subject_of(path: Path) -> str:
    """从文件名判断科目：文件名含「职测」算职测，其余（行测 / 国考 / 省考 / 联考）都算行测。"""
    name = Path(path).name
    return "职测" if "职测" in name else "行测"
