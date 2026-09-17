# -*- coding: utf-8 -*-
"""字段级生成器：加权抽样、时间、时长、金额、媒体占位文件（真实合法格式）"""
import base64
import datetime
import wave
from pathlib import Path

import config


def weighted_pick(rng, mapping):
    """按权重从 dict 中抽一个键：weighted_pick(rng, {"接通": 90, "未接": 8})"""
    return rng.choices(list(mapping.keys()), weights=list(mapping.values()), k=1)[0]


def rand_date_in_window(rng, start=config.WINDOW_START, end=config.WINDOW_END):
    start_d = datetime.date.fromisoformat(start)
    end_d = datetime.date.fromisoformat(end)
    days = (end_d - start_d).days + 1
    return start_d + datetime.timedelta(days=rng.randrange(days))


def rand_time_in_window(rng, hour_weights=config.HOUR_WEIGHTS):
    """窗口内随机时刻：先按小时权重抽小时（白天多、深夜少），再抽分秒"""
    day = rand_date_in_window(rng)
    hour = rng.choices(range(24), weights=hour_weights, k=1)[0]
    return datetime.datetime(day.year, day.month, day.day, hour, rng.randrange(60), rng.randrange(60))


def rand_duration(rng):
    """混合分布：10% 超短通话 [1,5] 秒 + 90% 对数正态 [5,3600] 秒（未接/拒接由调用方置 0）"""
    if rng.random() < 0.10:
        return rng.randrange(1, 6)
    v = int(rng.lognormvariate(3.2, 0.9))
    return max(5, min(3600, v))


def rand_amount(rng):
    return float(rng.choices(config.AMOUNT_CHOICES, weights=config.AMOUNT_WEIGHTS, k=1)[0])


# ---- 媒体占位文件：真实合法格式（1x1 PNG / 1 秒静音 WAV），不是 0 字节空文件 ----
_PNG_1X1_B64 = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
                "AAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


def save_png(path):
    Path(path).write_bytes(base64.b64decode(_PNG_1X1_B64))


def save_wav(path, seconds=1):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x00\x00" * (8000 * seconds))
