# -*- coding: utf-8 -*-
"""
清洗规则：唯一来源是 data_dict_v2.yaml（本文件是手写版翻译）
结构：required=必填 / regex=正则 / enum=枚举 / domain=数值域
"""
PHONE_RE = r"^1[3-9][0-9]{9}$"

RULES = {
    "call_records": {
        "required": ["call_id", "case_id", "caller", "callee", "call_time", "call_channel"],
        "regex": {"caller": PHONE_RE, "callee": PHONE_RE},
        "enum": {
            "call_channel": ["移动", "联通", "电信", "VoIP", "微信语音"],
            "call_type": ["接通", "未接", "拒接"],
        },
        "domain": {"duration": {"fn": lambda v: v >= 0, "msg": "必须 >= 0"}},
        "time_col": "call_time",
    },
    "transfer_records": {
        "required": ["transfer_id", "case_id", "from_account", "to_account",
                     "amount", "transfer_time", "transfer_channel"],
        "regex": {},
        "enum": {
            "transfer_channel": ["银行转账", "支付宝", "微信", "现金"],
            "transfer_type": ["扫码", "网银", "柜台"],
            "status": ["成功", "失败", "处理中"],
            "currency": ["CNY", "USD"],
        },
        "domain": {"amount": {"fn": lambda v: v >= 0, "msg": "必须 >= 0"}},
        "time_col": "transfer_time",
    },
    "chat_messages": {
        "required": ["message_id", "case_id", "sender_id", "receiver_id",
                     "chat_time", "chat_channel"],
        "regex": {},
        "enum": {
            "chat_channel": ["微信", "QQ", "短信", "钉钉"],
            "message_type": ["文本", "图片", "语音", "视频"],
        },
        "domain": {},
        "time_col": "chat_time",
    },
}

# 去重业务键：这几列完全相同 = 重复行
DEDUP_KEYS = {
    "call_records": ["caller", "callee", "call_time"],
    "transfer_records": ["from_account", "to_account", "amount", "transfer_time"],
    "chat_messages": ["sender_id", "receiver_id", "chat_time", "message_content"],
}
