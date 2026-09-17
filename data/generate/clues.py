# -*- coding: utf-8 -*-
"""三条线索植入：固定人物对 + 与字典字段精确联动；同步收集 evidence_ids 写 golden"""
import datetime
import uuid

import config
import fields
import persons


def _id(rng):
    # 从 rng 生成确定性 UUID：uuid4() 用系统熵，会破坏"同种子可复现"
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def reserved_pairs(pool):
    """线索专用号码对：噪声生成必须避开，保证 golden 答案唯一"""
    zhang = persons.by_name(pool, config.SUSPECT_NAME)
    pairs = set()
    for name in config.ASSOCIATE_NAMES[:3]:   # 李四/王五/刘六
        pairs.add(frozenset((zhang["phone"], persons.by_name(pool, name)["phone"])))
    return pairs


def expected_counts(scale):
    """噪声配置数 + 线索增量 = 最终总行数（自检用）"""
    c = config.SCALES[scale]
    clue_calls = config.CLUE1_CALLS[scale] + 1 + 1          # 线索1凌晨通话 + 线索2通话 + 线索3通话
    clue_transfers = 2                                      # 线索1 + 线索2
    clue_chats = len(config.CLUE2_TEXTS) + len(config.CLUE3_TEXTS)
    return {"calls": c["calls"] + clue_calls,
            "transfers": c["transfers"] + clue_transfers,
            "chats": c["chats"] + clue_chats}


def plant_clue_1(rng, cfg, pool, calls, transfers, golden_items):
    """线索1（直接）：张三-李四 凌晨 2~4 点高频通话 + 8888 元转账"""
    a = persons.by_name(pool, config.SUSPECT_NAME)
    b = persons.by_name(pool, "李四")
    n = config.CLUE1_CALLS[cfg["scale"]]
    call_ids, times = [], []
    for _ in range(n):
        day = fields.rand_date_in_window(rng)
        t = datetime.datetime(day.year, day.month, day.day, rng.choice([2, 3]),
                              rng.randrange(60), rng.randrange(60))
        cid = _id(rng)
        calls.append({
            "call_id": cid, "case_id": config.CASE_ID,
            "caller": a["phone"], "callee": b["phone"],
            "call_time": t.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": rng.randint(900, 1800),   # 15~30 分钟
            "call_channel": fields.weighted_pick(rng, config.CALL_CHANNEL_WEIGHTS),
            "call_type": "接通",
            "location": rng.choice(config.CALL_LOCATIONS),
            "content": "", "embedding_id": "", "raw_data": "",
        })
        call_ids.append(cid)
        times.append(t)
    # 转账在最后一次通话之后 10~60 分钟
    t_time = max(times) + datetime.timedelta(minutes=rng.randint(10, 60))
    tid = _id(rng)
    transfers.append({
        "transfer_id": tid, "case_id": config.CASE_ID,
        "from_account": a["phone"], "to_account": b["phone"],
        "amount": f"{config.CLUE1_AMOUNT:.2f}", "currency": "CNY",
        "transfer_time": t_time.strftime("%Y-%m-%d %H:%M:%S"),
        "transfer_channel": "微信", "transfer_type": "扫码",
        "remark": "货款", "status": "成功",
        "embedding_id": "", "raw_data": "",
    })
    golden_items.append({
        "item_id": "G-01", "clue_type": "clue_1",
        "question": f"找出与{config.SUSPECT_NAME}凌晨频繁联系且有资金往来的人",
        "answer_entities": ["李四"],
        "evidence_ids": {"call_record": call_ids, "transfer_record": [tid], "chat_message": []},
        "timeline": [
            {"time": times[0].strftime("%Y-%m-%d %H:%M:%S"),
             "event": f"{config.SUSPECT_NAME}与李四凌晨首次通话（共 {n} 次）"},
            {"time": t_time.strftime("%Y-%m-%d %H:%M:%S"),
             "event": f"{config.SUSPECT_NAME}向李四转账 {config.CLUE1_AMOUNT:.0f} 元"},
        ],
        "verifiable_sql": (f"SELECT caller, callee, COUNT(*) FROM call_record "
                           f"WHERE HOUR(call_time) BETWEEN 2 AND 4 "
                           f"GROUP BY caller, callee HAVING COUNT(*) >= {n}"),
    })
    return calls, transfers, golden_items


def plant_clue_2(rng, cfg, pool, calls, transfers, chats, golden_items):
    """线索2（暗语）：张三-王五 同日 暗语聊天 + 通话 + 带暗语附言的转账"""
    a = persons.by_name(pool, config.SUSPECT_NAME)
    c = persons.by_name(pool, "王五")
    day = fields.rand_date_in_window(rng)
    # 1 次通话（当天 19:30 左右）
    call_t = datetime.datetime(day.year, day.month, day.day, 19, rng.randrange(0, 30))
    call_id = _id(rng)
    calls.append({
        "call_id": call_id, "case_id": config.CASE_ID,
        "caller": a["phone"], "callee": c["phone"],
        "call_time": call_t.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": rng.randint(300, 600),
        "call_channel": fields.weighted_pick(rng, config.CALL_CHANNEL_WEIGHTS),
        "call_type": "接通", "location": rng.choice(config.CALL_LOCATIONS),
        "content": "", "embedding_id": "", "raw_data": "",
    })
    # 暗语聊天（当天 20:00 起，双方交替）
    chat_ids = []
    for i, text in enumerate(config.CLUE2_TEXTS):
        sender = a["phone"] if i % 2 == 0 else c["phone"]
        receiver = c["phone"] if i % 2 == 0 else a["phone"]
        t = datetime.datetime(day.year, day.month, day.day, 20, i * 7 + rng.randrange(0, 5))
        mid = _id(rng)
        chats.append({
            "message_id": mid, "case_id": config.CASE_ID,
            "sender_id": sender, "receiver_id": receiver,
            "chat_time": t.strftime("%Y-%m-%d %H:%M:%S"),
            "chat_channel": "微信", "message_type": "文本",
            "message_content": text, "media_url": "",
            "embedding_id": "", "raw_data": "",
        })
        chat_ids.append(mid)
    # 转账（21:30，附言带暗语）
    t_time = datetime.datetime(day.year, day.month, day.day, 21, rng.randrange(20, 40))
    tid = _id(rng)
    transfers.append({
        "transfer_id": tid, "case_id": config.CASE_ID,
        "from_account": c["phone"], "to_account": a["phone"],
        "amount": f"{config.CLUE2_AMOUNT:.2f}", "currency": "CNY",
        "transfer_time": t_time.strftime("%Y-%m-%d %H:%M:%S"),
        "transfer_channel": "微信", "transfer_type": "扫码",
        "remark": "老地方定金", "status": "成功",
        "embedding_id": "", "raw_data": "",
    })
    golden_items.append({
        "item_id": "G-02", "clue_type": "clue_2",
        "question": f"{config.SUSPECT_NAME}近期与谁有可疑的资金交易？",
        "answer_entities": ["王五"],
        "evidence_ids": {"call_record": [call_id], "transfer_record": [tid], "chat_message": chat_ids},
        "timeline": [
            {"time": call_t.strftime("%Y-%m-%d %H:%M:%S"), "event": f"{config.SUSPECT_NAME}与王五通话"},
            {"time": t_time.strftime("%Y-%m-%d %H:%M:%S"), "event": "王五向张三转账 6666 元（附言'老地方定金'）"},
        ],
        "verifiable_sql": "SELECT * FROM chat_message WHERE message_content LIKE '%走一趟%'",
    })
    return calls, transfers, chats, golden_items


def plant_clue_3(rng, cfg, pool, chats, calls, golden_items):
    """线索3（跨数据集）：聊天地点'城南仓库' = 话单基站'城南仓库基站'"""
    a = persons.by_name(pool, config.SUSPECT_NAME)
    d = persons.by_name(pool, "刘六")
    day = fields.rand_date_in_window(rng)
    chat_ids = []
    for i, text in enumerate(config.CLUE3_TEXTS):
        sender = d["phone"] if i == 0 else a["phone"]
        receiver = a["phone"] if i == 0 else d["phone"]
        t = datetime.datetime(day.year, day.month, day.day, 14, i * 10 + rng.randrange(0, 5))
        mid = _id(rng)
        chats.append({
            "message_id": mid, "case_id": config.CASE_ID,
            "sender_id": sender, "receiver_id": receiver,
            "chat_time": t.strftime("%Y-%m-%d %H:%M:%S"),
            "chat_channel": "微信", "message_type": "文本",
            "message_content": text, "media_url": "",
            "embedding_id": "", "raw_data": "",
        })
        chat_ids.append(mid)
    # 当天 15:00 通话，基站=城南仓库基站（与聊天地点呼应）
    call_t = datetime.datetime(day.year, day.month, day.day, 15, rng.randrange(0, 20))
    call_id = _id(rng)
    calls.append({
        "call_id": call_id, "case_id": config.CASE_ID,
        "caller": a["phone"], "callee": d["phone"],
        "call_time": call_t.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": rng.randint(180, 300),
        "call_channel": "移动", "call_type": "接通",
        "location": config.CLUE3_LOCATION,
        "content": "", "embedding_id": "", "raw_data": "",
    })
    golden_items.append({
        "item_id": "G-03", "clue_type": "clue_3",
        "question": f"{config.SUSPECT_NAME}团伙的接头地点可能在哪里？",
        "answer_entities": ["城南仓库"],
        "evidence_ids": {"call_record": [call_id], "transfer_record": [], "chat_message": chat_ids},
        "timeline": [
            {"time": call_t.strftime("%Y-%m-%d %H:%M:%S"), "event": "通话基站为'城南仓库基站'"},
        ],
        "verifiable_sql": "SELECT * FROM call_record WHERE location='城南仓库基站'",
    })
    return chats, calls, golden_items
