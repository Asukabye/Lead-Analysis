# -*- coding: utf-8 -*-
"""人物池：1 嫌疑人 + 4 关联人 + 若干干扰人；号码保证匹配字典正则 ^1[3-9][0-9]{9}$"""
import config


def build_persons(rng, fake, cfg):
    """返回人物列表 [{name, phone, role}]；固定人物在前、干扰人在后，号码全局唯一"""
    persons = [{"name": config.SUSPECT_NAME, "phone": _phone(rng), "role": "suspect"}]
    for name in config.ASSOCIATE_NAMES:
        persons.append({"name": name, "phone": _phone(rng), "role": "associate"})
    used = {p["phone"] for p in persons}
    noise_count = cfg["persons"] - len(persons)
    for _ in range(max(0, noise_count)):
        while True:
            phone = _phone(rng)
            if phone not in used:
                used.add(phone)
                break
        persons.append({"name": fake.name(), "phone": phone, "role": "noise"})
    return persons


def by_name(pool, name):
    for p in pool:
        if p["name"] == name:
            return p
    raise ValueError(f"人物池中不存在：{name}")


def _phone(rng):
    """1 + 一位[3-9] + 9 位数字 = 11 位，满足 ^1[3-9][0-9]{9}$"""
    return "1" + rng.choice("3456789") + "".join(rng.choice("0123456789") for _ in range(9))
