# -*- coding: utf-8 -*-
"""golden 补充条目：事实题（生成时统计，SQL 可验证）+ 负面题（测幻觉）"""
import config
import persons


def build_extra_items(calls, pool):
    zhang = persons.by_name(pool, config.SUSPECT_NAME)
    jan_calls = [c for c in calls
                 if c["caller"] == zhang["phone"] and c["call_time"].startswith("2025-01")]
    fact = {
        "item_id": "G-04", "clue_type": "fact",
        "question": f"{config.SUSPECT_NAME}在 2025 年 1 月的通话总次数是多少？",
        "answer_entities": [],
        "expected_fact": {"calls_in_jan": len(jan_calls)},
        "evidence_ids": {"call_record": [c["call_id"] for c in jan_calls],
                         "transfer_record": [], "chat_message": []},
        "verifiable_sql": (f"SELECT COUNT(*) FROM call_record WHERE caller='{zhang['phone']}' "
                           "AND call_time BETWEEN '2025-01-01' AND '2025-01-31'"),
    }
    negative = {
        "item_id": "G-05", "clue_type": "negative",
        "question": f"{config.SUSPECT_NAME}与手机号 {config.NEGATIVE_PHONE} 的人有什么关联？",
        "answer_entities": [],
        "expected_answer": "无关联（该号码不在数据中）",
        "evidence_ids": {},
        "verifiable_sql": (f"SELECT COUNT(*) FROM call_record WHERE caller='{config.NEGATIVE_PHONE}' "
                           f"OR callee='{config.NEGATIVE_PHONE}'"),
    }
    return [fact, negative]
