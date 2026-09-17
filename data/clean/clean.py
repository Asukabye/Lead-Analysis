# -*- coding: utf-8 -*-
"""
清洗流水线：read → normalize → validate → split → dedup → 写盘+报告
用法：python clean.py --csv 数据.csv --table call_records [--out-dir cleaned]
"""
import argparse
import json
from pathlib import Path

import pandas as pd

import rules


def read_csv_safe(path):
    # utf-8-sig：去掉 BOM；keep_default_na=False：空串保持空串（不被读成 NaN）
    return pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)


def normalize(df, table):
    df = df.copy()
    # 1) 文本列：去首尾空白，空串 → None（字典 nullable 语义）
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace("", None)
    # 2) 时间列：解析成 datetime，非法值变 NaT（校验阶段会被拦下）
    t = rules.RULES[table]["time_col"]
    df[t] = pd.to_datetime(df[t], errors="coerce")
    return df


def validate(df, table):
    r = rules.RULES[table]
    df = df.copy()
    df["err_reason"] = None

    def mark(mask, reason):
        df.loc[mask & df["err_reason"].isna(), "err_reason"] = reason

    # 1) 必填（时间列的 NaT 也会被 isna 命中）
    for col in r["required"]:
        mark(df[col].isna(), f"缺失必填字段 {col}")
    # 2) 正则
    for col, pattern in r["regex"].items():
        mark(df[col].notna() & ~df[col].astype(str).str.match(pattern), f"{col} 格式非法")
    # 3) 枚举（nullable 字段允许为空，只拦"非空的非法值"）
    for col, values in r["enum"].items():
        mark(df[col].notna() & ~df[col].isin(values), f"{col} 枚举非法")
    # 4) 数值域（金额/时长：先转数值，NaN 或违反 domain 都拒）
    for col, spec in r["domain"].items():
        numeric = pd.to_numeric(df[col], errors="coerce")
        mark(numeric.isna() | ~spec["fn"](numeric), f"{col} {spec['msg']}")
    return df


def split(df):
    clean = df[df["err_reason"].isna()].drop(columns=["err_reason"])
    rejected = df[df["err_reason"].notna()]
    return clean, rejected


def dedup(df, table):
    before = len(df)
    df = df.drop_duplicates(subset=rules.DEDUP_KEYS[table])
    return df, before - len(df)


def run_clean(csv_path, table, out_dir=None):
    """返回统计 dict；给 out_dir 时同时写 clean/rejected/report 三个文件"""
    df = read_csv_safe(csv_path)
    total = len(df)
    df = normalize(df, table)
    df = validate(df, table)
    clean, rejected = split(df)
    clean, n_dup = dedup(clean, table)
    errors = rejected["err_reason"].value_counts().to_dict()
    result = {"table": table, "total": total, "clean": len(clean),
              "rejected": len(rejected), "deduped": n_dup,
              "errors": {str(k): int(v) for k, v in errors.items()}}
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        stem = Path(csv_path).stem
        clean.to_csv(out / f"{stem}.csv", index=False, encoding="utf-8-sig")
        rejected.to_csv(out / f"{stem}_rejected.csv", index=False, encoding="utf-8-sig")
        (out / f"{stem}_report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="清洗流水线")
    ap.add_argument("--csv", required=True, help="输入 CSV 路径")
    ap.add_argument("--table", required=True, choices=list(rules.RULES), help="表名")
    ap.add_argument("--out-dir", default=None, help="输出目录（不传只打印统计）")
    args = ap.parse_args()
    r = run_clean(args.csv, args.table, args.out_dir)
    print(json.dumps(r, ensure_ascii=False, indent=2))
