# -*- coding: utf-8 -*-
"""导入脚本验收（SQLite 测试库）：python -m pytest test_import.py -v"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import db           # noqa: E402
import import_csv   # noqa: E402

HEADER = ("call_id,case_id,caller,callee,call_time,duration,call_channel,"
          "call_type,location,content,embedding_id,raw_data")
GOOD_ROW = "id-1,C001,13812345678,13987654321,2025-01-01 10:00:00,60,移动,接通,城东基站-01,,,"


@pytest.fixture
def uri(tmp_path):
    return f"sqlite:///{tmp_path / 'test.db'}"


def _make_csv(tmp_path, lines):
    p = tmp_path / "call_records.csv"
    p.write_text("\n".join(lines), encoding="utf-8-sig")
    return str(p)


def test_idempotent(uri, tmp_path):
    """验收 1：幂等——第二次导入 skipped，行数不变，日志不新增"""
    csv = _make_csv(tmp_path, [HEADER, GOOD_ROW])
    assert import_csv.run_import(csv, "call_record", "C001", uri) == "ok"
    assert import_csv.run_import(csv, "call_record", "C001", uri) == "skipped"
    conn = db.connect(uri)
    assert db.exec_sql(conn, "SELECT COUNT(*) FROM call_record").fetchone()[0] == 1
    assert db.exec_sql(conn, "SELECT COUNT(*) FROM import_log").fetchone()[0] == 1


def test_rollback(uri, tmp_path):
    """验收 2：回滚——坏行导致失败后数据零残留，失败日志已落库"""
    bad = "id-2,C001,,13987654321,2025-01-01 10:00:00,60,移动,接通,城东基站-01,,,"  # caller 空
    csv = _make_csv(tmp_path, [HEADER, GOOD_ROW, bad])
    with pytest.raises(Exception):
        import_csv.run_import(csv, "call_record", "C001", uri)
    conn = db.connect(uri)
    assert db.exec_sql(conn, "SELECT COUNT(*) FROM call_record").fetchone()[0] == 0  # 零残留
    assert db.exec_sql(conn, "SELECT status FROM import_log").fetchone()[0] == "失败"


def test_empty_numeric_becomes_null(uri, tmp_path):
    """验收 3：数值字段为空 → 导入成功且落库为 NULL（防 pymysql 报 'nan can not be used'）"""
    empty_duration = "id-1,C001,13812345678,13987654321,2025-01-01 10:00:00,,移动,接通,城东基站-01,,,"
    csv = _make_csv(tmp_path, [HEADER, empty_duration])
    assert import_csv.run_import(csv, "call_record", "C001", uri) == "ok"
    conn = db.connect(uri)
    row = db.exec_sql(conn, "SELECT duration FROM call_record").fetchone()
    assert row[0] is None, f"duration 应为 NULL，实际：{row[0]!r}"
