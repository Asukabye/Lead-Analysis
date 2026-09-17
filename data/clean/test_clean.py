# -*- coding: utf-8 -*-
"""清洗脚本验收：python -m pytest test_clean.py -v"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import clean  # noqa: E402

DIRTY = Path(__file__).parent / "dirty_samples" / "call_records_dirty.csv"


def test_dirty_samples():
    """9 行脏样本：6 行被拒、1 行去重、2 行通过"""
    r = clean.run_clean(str(DIRTY), "call_records")
    assert r["rejected"] == 6, f"应拒绝 6 行，实际：{r}"
    assert r["deduped"] == 1, f"应去重 1 行，实际：{r}"
    assert r["clean"] == 2, f"应通过 2 行，实际：{r}"


def test_generated_data_all_clean():
    """生成器产物应 100% 通过（生成器只产合法数据）"""
    gen = Path(__file__).parent.parent / "generate" / "out" / "call_records.csv"
    if not gen.exists():
        return  # 未生成数据时跳过
    r = clean.run_clean(str(gen), "call_records")
    assert r["rejected"] == 0 and r["deduped"] == 0, f"生成器数据不应被拒：{r}"
