# -*- coding: utf-8 -*-
"""
编排入口。
用法（在 generate 目录下执行）：
    python main.py --scale mini
    python main.py --scale dev  --seed 42 --out-dir out
依赖：pip install pandas faker
"""
import argparse
import hashlib
import json
import random
from pathlib import Path

import pandas as pd
from faker import Faker

import config
import clues
import fields
import golden
import noise
import persons
import quality_check

CSV_FILES = ["case_info.csv", "user_case_permission.csv", "call_records.csv",
             "transfer_records.csv", "chat_messages.csv", "golden.json"]


def run_generator(seed=config.DEFAULT_SEED, scale="mini", out_dir=None) -> Path:
    if scale not in config.SCALES:
        raise ValueError(f"未知规模：{scale}（可选 {list(config.SCALES)}）")
    cfg = dict(config.SCALES[scale])
    cfg["scale"] = scale
    out_dir = Path(out_dir) if out_dir else Path(__file__).parent / "out"
    media_dir = out_dir / config.MEDIA_DIR_NAME / config.CASE_ID
    media_dir.mkdir(parents=True, exist_ok=True)

    # 单一随机源（可复现的根）
    rng = random.Random(seed)
    fake = Faker("zh_CN")
    fake.seed_instance(seed)

    pool = persons.build_persons(rng, fake, cfg)
    reserved = clues.reserved_pairs(pool)

    calls = noise.gen_noise_calls(rng, cfg, pool, reserved)
    transfers = noise.gen_noise_transfers(rng, cfg, pool, reserved)
    chats = noise.gen_noise_chats(rng, cfg, pool, reserved, media_dir)

    golden_items = []
    calls, transfers, golden_items = clues.plant_clue_1(rng, cfg, pool, calls, transfers, golden_items)
    calls, transfers, chats, golden_items = clues.plant_clue_2(rng, cfg, pool, calls, transfers, chats, golden_items)
    chats, calls, golden_items = clues.plant_clue_3(rng, cfg, pool, chats, calls, golden_items)
    golden_items += golden.build_extra_items(calls, pool)

    _save_csvs(out_dir, pool, calls, transfers, chats)
    golden_doc = {"version": config.VERSION, "case_id": config.CASE_ID,
                  "seed": seed, "scale": scale, "items": golden_items}
    (out_dir / "golden.json").write_text(
        json.dumps(golden_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    _save_manifest(out_dir, seed, scale)

    quality_check.run(out_dir)   # 不合格 exit(1)，坏数据不放行
    return out_dir


def _save_csvs(out_dir, pool, calls, transfers, chats):
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [{"case_id": config.CASE_ID, "case_name": config.CASE_NAME,
          "case_status": "进行中", "owner_id": "u_admin", "description": "演示案件"}],
        columns=["case_id", "case_name", "case_status", "owner_id", "description"],
    ).to_csv(out_dir / "case_info.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [{"user_id": "u_admin", "case_id": config.CASE_ID, "role": "admin"},
         {"user_id": "u_viewer", "case_id": config.CASE_ID, "role": "viewer"}],
        columns=["user_id", "case_id", "role"],
    ).to_csv(out_dir / "user_case_permission.csv", index=False, encoding="utf-8-sig")
    _save(out_dir / "call_records.csv", calls,
          ["call_id", "case_id", "caller", "callee", "call_time", "duration",
           "call_channel", "call_type", "location", "content", "embedding_id", "raw_data"])
    _save(out_dir / "transfer_records.csv", transfers,
          ["transfer_id", "case_id", "from_account", "to_account", "amount", "currency",
           "transfer_time", "transfer_channel", "transfer_type", "remark", "status",
           "embedding_id", "raw_data"])
    _save(out_dir / "chat_messages.csv", chats,
          ["message_id", "case_id", "sender_id", "receiver_id", "chat_time", "chat_channel",
           "message_type", "message_content", "media_url", "embedding_id", "raw_data"])


def _save(path, rows, columns):
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save_manifest(out_dir, seed, scale):
    manifest = {"seed": seed, "scale": scale, "version": config.VERSION,
                "files": {f: _sha256(out_dir / f) for f in CSV_FILES}}
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Lead Analysis 模拟数据生成器")
    ap.add_argument("--scale", default="mini", choices=list(config.SCALES), help="规模档位")
    ap.add_argument("--seed", type=int, default=config.DEFAULT_SEED, help="随机种子（同种子输出一致）")
    ap.add_argument("--out-dir", default=None, help="输出目录（默认 ./out）")
    args = ap.parse_args()
    out = run_generator(seed=args.seed, scale=args.scale, out_dir=args.out_dir)
    print(f"生成完成：{out}")
