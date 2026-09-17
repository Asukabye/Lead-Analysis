# -*- coding: utf-8 -*-
"""
一次性导入全部产物（按外键顺序）。
用法：
  python run_all.py --data-dir ../generate/out/cleaned --db sqlite:///test.db
  真库：--db "mysql+pymysql://root:密码@localhost/lead_analysis"
"""
import argparse
from pathlib import Path

import import_csv

ORDER = ["case_info", "user_case_permission", "call_records", "transfer_records", "chat_messages"]

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="按外键顺序批量导入")
    ap.add_argument("--data-dir", default="../generate/out/cleaned", help="清洗后数据目录")
    ap.add_argument("--case-id", default="C001")
    ap.add_argument("--db", default="mysql+pymysql://root:123456@localhost/lead_analysis")
    args = ap.parse_args()
    data = Path(args.data_dir)
    for name in ORDER:
        csv = data / f"{name}.csv"
        if not csv.exists():
            print(f"[miss] {csv} 不存在，跳过")
            continue
        import_csv.run_import(str(csv), import_csv.TABLE_OF_CSV[name], args.case_id, args.db)
