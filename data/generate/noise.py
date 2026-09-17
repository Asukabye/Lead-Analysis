# -*- coding: utf-8 -*-
"""干扰数据生成（背景噪声，占总量 95%+）：不碰线索专用号码对，字段满足字典约束且相互联动"""
import uuid

import config
import fields


def _id(rng):
    # 从 rng 生成确定性 UUID：uuid4() 用系统熵，会破坏"同种子可复现"
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))   # 36 字符，匹配 CHAR(36)


def gen_noise_calls(rng, cfg, persons, reserved_pairs):
    rows = []
    phones = [p["phone"] for p in persons]
    while len(rows) < cfg["calls"]:
        a, b = rng.sample(phones, 2)
        if frozenset((a, b)) in reserved_pairs:      # 避开线索号码对，保证 golden 答案唯一
            continue
        call_time = fields.rand_time_in_window(rng)
        call_type = fields.weighted_pick(rng, config.CALL_TYPE_WEIGHTS)
        duration = 0 if call_type in ("未接", "拒接") else fields.rand_duration(rng)
        content = rng.choice(config.CALL_TRANSCRIPTS) if rng.random() < config.CALL_CONTENT_RATIO else ""
        rows.append({
            "call_id": _id(rng), "case_id": config.CASE_ID,
            "caller": a, "callee": b,
            "call_time": call_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": duration,
            "call_channel": fields.weighted_pick(rng, config.CALL_CHANNEL_WEIGHTS),
            "call_type": call_type,
            "location": rng.choice(config.CALL_LOCATIONS),   # 不用线索3专用基站
            "content": content,
            "embedding_id": "", "raw_data": "",
        })
    return rows


def gen_noise_transfers(rng, cfg, persons, reserved_pairs):
    rows = []
    phones = [p["phone"] for p in persons]
    while len(rows) < cfg["transfers"]:
        frm, to = rng.sample(phones, 2)
        if frozenset((frm, to)) in reserved_pairs:
            continue
        channel = fields.weighted_pick(rng, config.TRANSFER_CHANNEL_WEIGHTS)
        rows.append({
            "transfer_id": _id(rng), "case_id": config.CASE_ID,
            "from_account": frm, "to_account": to,
            "amount": f"{fields.rand_amount(rng):.2f}", "currency": "CNY",
            "transfer_time": fields.rand_time_in_window(rng).strftime("%Y-%m-%d %H:%M:%S"),
            "transfer_channel": channel,
            "transfer_type": config.CHANNEL_TYPE_MAP[channel],   # 渠道与方式联动
            "remark": rng.choice(config.TRANSFER_REMARKS),
            "status": fields.weighted_pick(rng, config.TRANSFER_STATUS_WEIGHTS),
            "embedding_id": "", "raw_data": "",
        })
    return rows


def gen_noise_chats(rng, cfg, persons, reserved_pairs, media_dir):
    """文本走模板；图片/语音创建占位媒体文件，media_url 与 message_type 联动"""
    rows = []
    phones = [p["phone"] for p in persons]
    counter = 0
    while len(rows) < cfg["chats"]:
        sender, receiver = rng.sample(phones, 2)
        if frozenset((sender, receiver)) in reserved_pairs:
            continue
        mtype = fields.weighted_pick(rng, config.MESSAGE_TYPE_WEIGHTS)
        if mtype == "文本":
            content, media_url = rng.choice(config.CHAT_TEMPLATES), ""
        elif mtype == "图片":
            counter += 1
            fname = f"img_{counter:04d}.png"
            fields.save_png(media_dir / fname)
            content, media_url = "", f"/data/media/{config.CASE_ID}/{fname}"
        else:  # 语音
            counter += 1
            fname = f"audio_{counter:04d}.wav"
            fields.save_wav(media_dir / fname)
            content, media_url = "", f"/data/media/{config.CASE_ID}/{fname}"
        rows.append({
            "message_id": _id(rng), "case_id": config.CASE_ID,
            "sender_id": sender, "receiver_id": receiver,
            "chat_time": fields.rand_time_in_window(rng).strftime("%Y-%m-%d %H:%M:%S"),
            "chat_channel": fields.weighted_pick(rng, config.CHAT_CHANNEL_WEIGHTS),
            "message_type": mtype,
            "message_content": content, "media_url": media_url,
            "embedding_id": "", "raw_data": "",
        })
    return rows
