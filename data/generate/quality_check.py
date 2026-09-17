# -*- coding: utf-8 -*-
"""生成后自检：pandas 逐项断言字典约束，任何一项失败打印明细并 exit(1)"""
import json
import re
import sys

import pandas as pd

import config
import clues

PHONE_RE = re.compile(r"^1[3-9][0-9]{9}$")
ID_COL = {"call_record": "call_id", "transfer_record": "transfer_id", "chat_message": "message_id"}


def run(out_dir):
    calls = pd.read_csv(out_dir / "call_records.csv", parse_dates=["call_time"], keep_default_na=False)
    transfers = pd.read_csv(out_dir / "transfer_records.csv", parse_dates=["transfer_time"], keep_default_na=False)
    chats = pd.read_csv(out_dir / "chat_messages.csv", parse_dates=["chat_time"], keep_default_na=False)
    golden = json.loads((out_dir / "golden.json").read_text(encoding="utf-8"))
    scale = golden["scale"]

    failures = []

    def check(name, ok):
        if not ok:
            failures.append(name)

    # 1) 行数 = 噪声配置 + 线索增量
    exp = clues.expected_counts(scale)
    check(f"话单行数(期望{exp['calls']})", len(calls) == exp["calls"])
    check(f"转账行数(期望{exp['transfers']})", len(transfers) == exp["transfers"])
    check(f"聊天行数(期望{exp['chats']})", len(chats) == exp["chats"])

    # 2) 非空 / 正则 / 枚举 / 数值域（对应字典 nullable/enum/domain）
    check("caller 无空值", calls["caller"].notna().all())
    check("caller 正则", calls["caller"].astype(str).str.match(PHONE_RE).all())
    check("callee 正则", calls["callee"].astype(str).str.match(PHONE_RE).all())
    check("call_channel 枚举", calls["call_channel"].isin(list(config.CALL_CHANNEL_WEIGHTS)).all())
    check("call_type 枚举", calls["call_type"].isin(list(config.CALL_TYPE_WEIGHTS)).all())
    check("duration 非负", (calls["duration"] >= 0).all())
    check("未接/拒接时长为0", (calls[calls["call_type"].isin(["未接", "拒接"])]["duration"] == 0).all())
    check("时间在案发窗口内", calls["call_time"].between("2025-01-01", "2025-03-31 23:59:59").all())
    check("amount 非负", (pd.to_numeric(transfers["amount"]) >= 0).all())
    check("transfer_channel 枚举", transfers["transfer_channel"].isin(list(config.TRANSFER_CHANNEL_WEIGHTS)).all())
    check("status 枚举", transfers["status"].isin(list(config.TRANSFER_STATUS_WEIGHTS)).all())
    check("message_type 枚举", chats["message_type"].isin(list(config.MESSAGE_TYPE_WEIGHTS)).all())

    # 3) 字段联动
    check("图片/语音必有media_url", (chats[chats["message_type"].isin(["图片", "语音"])]["media_url"] != "").all())
    check("文本必无media_url", (chats[chats["message_type"] == "文本"]["media_url"] == "").all())

    # 4) 线索存在性
    g1 = _item(golden, "G-01")
    row0 = calls[calls["call_id"] == g1["evidence_ids"]["call_record"][0]].iloc[0]
    a, b = row0["caller"], row0["callee"]
    night = calls[calls["call_time"].dt.hour.isin([2, 3])]
    night = night[((night["caller"] == a) & (night["callee"] == b))
                  | ((night["caller"] == b) & (night["callee"] == a))]
    check(f"线索1凌晨通话≥{config.CLUE1_CALLS[scale]}次", len(night) >= config.CLUE1_CALLS[scale])
    g1t = transfers[transfers["transfer_id"] == g1["evidence_ids"]["transfer_record"][0]].iloc[0]
    check("线索1大额转账存在", float(g1t["amount"]) == config.CLUE1_AMOUNT)
    check("线索2暗语存在", chats["message_content"].astype(str).str.contains("走一趟").any())
    check("线索3基站匹配", (calls["location"] == config.CLUE3_LOCATION).any())
    check("线索3地点暗语", chats["message_content"].astype(str).str.contains("城南仓库").any())

    # 5) golden 证据可查回
    for it in golden["items"]:
        for table, ids in it["evidence_ids"].items():
            df = {"call_record": calls, "transfer_record": transfers, "chat_message": chats}[table]
            missing = set(ids) - set(df[ID_COL[table]].astype(str))
            check(f"{it['item_id']} {table} 证据可查回", not missing)

    # 6) 事实题与负面题
    g4 = _item(golden, "G-04")
    check("事实题统计一致", g4["expected_fact"]["calls_in_jan"] == len(g4["evidence_ids"]["call_record"]))
    check("负面号码确实不存在",
          not ((calls["caller"] == config.NEGATIVE_PHONE)
               | (calls["callee"] == config.NEGATIVE_PHONE)).any())

    if failures:
        for f in failures:
            print(f"[FAIL] {f}")
        print(f"自检失败：{len(failures)} 项未通过")
        sys.exit(1)
    print(f"[PASS] 自检全部通过（{len(calls) + len(transfers) + len(chats)} 行）")


def _item(golden, item_id):
    return next(it for it in golden["items"] if it["item_id"] == item_id)
