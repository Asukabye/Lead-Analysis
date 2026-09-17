# -*- coding: utf-8 -*-
"""连接抽象：一套代码跑两种库（SQLite 单测 / MySQL 真库），SQLite 测试库自动建表"""
import sqlite3

try:
    import pymysql          # 仅 MySQL 路径需要；没装时 SQLite 单测不受影响
except ImportError:
    pymysql = None

# SQLite 测试库建表（与 MySQL 版对应：JSON→TEXT；去掉引擎/字符集/UUID 表达式默认值）
SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS case_info (
  case_id TEXT PRIMARY KEY, case_name TEXT NOT NULL, case_status TEXT NOT NULL DEFAULT '进行中',
  owner_id TEXT, description TEXT, create_time TEXT DEFAULT CURRENT_TIMESTAMP,
  update_time TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS user_case_permission (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, case_id TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'viewer', create_time TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, case_id)
);
CREATE TABLE IF NOT EXISTS call_record (
  call_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, caller TEXT NOT NULL, callee TEXT NOT NULL,
  call_time TEXT NOT NULL, duration INTEGER, call_channel TEXT NOT NULL, call_type TEXT,
  location TEXT, content TEXT, embedding_id TEXT, raw_data TEXT,
  create_time TEXT DEFAULT CURRENT_TIMESTAMP, update_time TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS transfer_record (
  transfer_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, from_account TEXT NOT NULL,
  to_account TEXT NOT NULL, amount TEXT NOT NULL, currency TEXT DEFAULT 'CNY',
  transfer_time TEXT NOT NULL, transfer_channel TEXT NOT NULL, transfer_type TEXT,
  remark TEXT, status TEXT DEFAULT '成功', embedding_id TEXT, raw_data TEXT,
  create_time TEXT DEFAULT CURRENT_TIMESTAMP, update_time TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chat_message (
  message_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, sender_id TEXT NOT NULL,
  receiver_id TEXT NOT NULL, chat_time TEXT NOT NULL, chat_channel TEXT NOT NULL,
  message_type TEXT DEFAULT '文本', message_content TEXT, media_url TEXT,
  embedding_id TEXT, raw_data TEXT,
  create_time TEXT DEFAULT CURRENT_TIMESTAMP, update_time TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS import_log (
  batch_id TEXT PRIMARY KEY, file_name TEXT NOT NULL, file_hash TEXT NOT NULL,
  case_id TEXT NOT NULL, table_name TEXT NOT NULL, total_rows INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT '成功', create_time TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (case_id, table_name, file_hash)
);
"""


def connect(uri):
    """sqlite:///test.db 或 mysql+pymysql://user:pwd@host:port/dbname"""
    if uri.startswith("sqlite"):
        conn = sqlite3.connect(uri.split("///", 1)[1])
        conn.executescript(SQLITE_SCHEMA)   # 测试库自动建表
        return conn
    rest = uri.split("://", 1)[1]
    if pymysql is None:
        raise RuntimeError("使用 MySQL 前请先执行：pip install pymysql")
    auth, host_db = rest.rsplit("@", 1)
    user, pwd = auth.split(":", 1)
    host_port, dbname = host_db.rsplit("/", 1)
    host = host_port.split(":")[0]
    port = int(host_port.split(":")[1]) if ":" in host_port else 3306
    return pymysql.connect(host=host, port=port, user=user, password=pwd,
                           database=dbname, charset="utf8mb4")


def ph(conn):
    """SQL 占位符：MySQL 用 %s，SQLite 用 ?"""
    return "?" if isinstance(conn, sqlite3.Connection) else "%s"


def begin(conn):
    if isinstance(conn, sqlite3.Connection):
        conn.execute("BEGIN")
    else:
        conn.begin()


def exec_sql(conn, sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def insert_many(conn, sql, rows):
    cur = conn.cursor()
    cur.executemany(sql, rows)
