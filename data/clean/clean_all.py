# -*- coding: utf-8 -*-
"""批量清洗生成器全部产物 → 输出到 cleaned/ 目录（文件名与原文件一致，供导入脚本使用）"""
import argparse
import shutil
from pathlib import Path

import clean

TABLES = {"call_records.csv": "call_records",
          "transfer_records.csv": "transfer_records",
          "chat_messages.csv": "chat_messages"}

# 基础表没有清洗规则，原样透传到 cleaned/（导入脚本按外键顺序需要它们）
PASS_THROUGH = ["case_info.csv", "user_case_permission.csv"]

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="批量清洗生成器产物")
    ap.add_argument("--data-dir", default="../generate/out", help="生成器输出目录")
    ap.add_argument("--out-dir", default="../generate/out/cleaned", help="清洗后输出目录")
    args = ap.parse_args()
    data = Path(args.data_dir)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for csv_name, table in TABLES.items():
        r = clean.run_clean(str(data / csv_name), table, args.out_dir)
        print(f"{csv_name}: 通过 {r['clean']} 行, 拒绝 {r['rejected']} 行, 去重 {r['deduped']} 行")
    for name in PASS_THROUGH:
        src = data / name
        if src.exists():
            shutil.copyfile(src, out / name)
            print(f"{name}: 原样透传")
