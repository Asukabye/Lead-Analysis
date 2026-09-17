# -*- coding: utf-8 -*-
"""
导入脚本：幂等（sha256 + import_log 唯一键）、批量 INSERT、事务回滚、日志、事后对账
用法：
  python import_csv.py --csv 文件.csv --table call_record --case-id C001 --db sqlite:///test.db
  真库：--db "mysql+pymysql://root:密码@localhost/lead_analysis"
"""
import argparse
import hashlib
import math
import uuid
from pathlib import Path

import pandas as pd

import db

# CSV 文件名 → 数据库表名 → 列白名单（防注入；不含 create/update_time，由 DB 默认值填）
TABLE_OF_CSV = {"case_info": "case_info", "user_case_permission": "user_case_permission",
                "call_records": "call_record", "transfer_records": "transfer_record",
                "chat_messages": "chat_message"}

COLUMNS = {
    "case_info": ["case_id", "case_name", "case_status", "owner_id", "description"],
    "user_case_permission": ["user_id", "case_id", "role"],
    "call_record": ["call_id", "case_id", "caller", "callee", "call_time", "duration",
                    "call_channel", "call_type", "location", "content", "embedding_id", "raw_data"],
    "transfer_record": ["transfer_id", "case_id", "from_account", "to_account", "amount",
                        "currency", "transfer_time", "transfer_channel", "transfer_type",
                        "remark", "status", "embedding_id", "raw_data"],
    "chat_message": ["message_id", "case_id", "sender_id", "receiver_id", "chat_time",
                     "chat_channel", "message_type", "message_content", "media_url",
                     "embedding_id", "raw_data"],
}

BATCH_SIZE = 5000


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def already_imported(conn, case_id, table, file_hash):
    p = db.ph(conn)
    cur = db.exec_sql(conn,
                      f"SELECT 1 FROM import_log WHERE case_id={p} AND table_name={p} AND file_hash={p}",
                      (case_id, table, file_hash))
    return cur.fetchone() is not None


def read_rows(csv_path, columns):
    """读 CSV（utf-8-sig）：空串与 NaN/NaT 统一转 None——pymysql 不接受 NaN（报 "nan can not be used"），None 落库为 SQL NULL"""
    df = pd.read_csv(csv_path, encoding="utf-8-sig", keep_default_na=False)
    df = df.where(df != "", None)          # 空串 → None

    def clean(v):
        if v is None or v is pd.NA:        # 空值 / pandas 缺失值
            return None
        if isinstance(v, float) and math.isnan(v):   # 双保险：单单元格 NaN 兜底
            return None
        return v

    return [tuple(clean(v) for v in row) for row in df[columns].itertuples(index=False, name=None)]


def insert_batch(conn, table, rows):
    cols = COLUMNS[table]
    placeholders = ", ".join([db.ph(conn)] * len(cols))
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
    cur = conn.cursor()
    for i in range(0, len(rows), BATCH_SIZE):
        cur.executemany(sql, rows[i:i + BATCH_SIZE])


def write_log(conn, case_id, table, file_name, file_hash, total_rows, status):
    p = db.ph(conn)
    db.exec_sql(conn,
                "INSERT INTO import_log (batch_id, file_name, file_hash, case_id, table_name, total_rows, status) "
                f"VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p})",
                (str(uuid.uuid4()), file_name, file_hash, case_id, table, total_rows, status))


def assert_count(conn, table, expected):
    cur = db.exec_sql(conn, f"SELECT COUNT(*) FROM {table}")
    actual = cur.fetchone()[0]
    if actual != expected:
        raise AssertionError(f"对账失败：{table} 期望 {expected} 行，实际 {actual} 行")


def run_import(csv_path, table, case_id, db_uri):
    """返回 'ok' / 'skipped'；失败抛异常（数据已回滚、失败日志已落库）"""
    file_name = Path(csv_path).name
    file_hash = sha256(csv_path)
    conn = db.connect(db_uri)
    try:
        if already_imported(conn, case_id, table, file_hash):
            print(f"[skipped] {file_name} 已导入过（{case_id}.{table}）")
            return "skipped"
        rows = read_rows(csv_path, COLUMNS[table])
        db.begin(conn)                              # 事务开始
        insert_batch(conn, table, rows)
        write_log(conn, case_id, table, file_name, file_hash, len(rows), "成功")
        conn.commit()                               # 一次性生效
    except Exception:
        conn.rollback()                             # 数据零残留
        # 失败日志必须用新连接写（否则被回滚掉），而且新连接也必须显式提交
        log_conn = db.connect(db_uri)
        write_log(log_conn, case_id, table, file_name, file_hash, 0, "失败")
        log_conn.commit()
        raise
    assert_count(conn, table, len(rows))            # 事后对账
    print(f"[ok] {table} 导入 {len(rows)} 行（{file_name}）")
    return "ok"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="导入 CSV 到数据库（幂等/回滚/日志/对账）")
    ap.add_argument("--csv", required=True, help="清洗后的 CSV 路径")
    ap.add_argument("--table", required=True, choices=list(COLUMNS), help="数据库表名")
    ap.add_argument("--case-id", default="C001")
    ap.add_argument("--db", default="sqlite:///test.db",
                    help="连接串，如 mysql+pymysql://root:密码@localhost/lead_analysis")
    args = ap.parse_args()
    run_import(args.csv, args.table, args.case_id, args.db)
