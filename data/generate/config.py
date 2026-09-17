# -*- coding: utf-8 -*-
"""
全局配置：规模、种子、路径、概率参数。
原则：所有"可调参数"集中在这个文件，其他模块一律从这里取值。
"""
from pathlib import Path

# ---- 三档规模（聊天 > 通话 > 转账，符合真实比例） ----
SCALES = {
    "mini":  {"persons": 10,  "calls": 50,    "chats": 150,    "transfers": 12},
    "dev":   {"persons": 50,  "calls": 8000,  "chats": 20000,  "transfers": 1200},
    "bench": {"persons": 500, "calls": 100000, "chats": 25000, "transfers": 8000},
}

DEFAULT_SEED = 42
VERSION = "1.0"

# ---- 案件与时间窗口 ----
CASE_ID = "C001"
CASE_NAME = "1·15 专案"
WINDOW_START = "2025-01-01"
WINDOW_END = "2025-03-31"

# ---- 人物池 ----
SUSPECT_NAME = "张三"                                # 嫌疑人（所有线索的中心人物）
ASSOCIATE_NAMES = ["李四", "王五", "刘六", "陈七"]     # 李四=线索1 / 王五=线索2 / 刘六=线索3 / 陈七=干扰关联人
NEGATIVE_PHONE = "19900009999"                       # 负面题用：数据中不存在的号码

# ---- 话单参数 ----
# 一天 24 小时权重：白天(8-18)高、深夜(0-6)低
HOUR_WEIGHTS = [1, 1, 1, 2, 2, 3, 5, 8, 10, 10, 10, 10, 10, 10, 10, 9, 8, 7, 6, 5, 4, 3, 2, 2]
CALL_TYPE_WEIGHTS = {"接通": 90, "未接": 8, "拒接": 2}
CALL_CHANNEL_WEIGHTS = {"移动": 30, "联通": 30, "电信": 30, "VoIP": 5, "微信语音": 5}
CALL_LOCATIONS = ["城东基站-01", "城东基站-03", "城西基站-07", "北站基站-02", "大学城基站-05", "火车站基站-01"]
CLUE3_LOCATION = "城南仓库基站"      # 线索3专用基站：噪声不用它，保持线索唯一性
CALL_CONTENT_RATIO = 0.05           # 5% 的通话生成转写摘要
CALL_TRANSCRIPTS = ["嗯，好的，那先这样。", "你到了给我打电话。", "明天几点？我再确认一下。", "东西都准备好了吗？"]

# ---- 转账参数 ----
AMOUNT_CHOICES = [50, 100, 200, 500, 888]
AMOUNT_WEIGHTS = [5, 4, 3, 1, 1]
TRANSFER_CHANNEL_WEIGHTS = {"微信": 40, "支付宝": 35, "银行转账": 20, "现金": 5}
TRANSFER_STATUS_WEIGHTS = {"成功": 95, "失败": 3, "处理中": 2}
TRANSFER_REMARKS = ["", "", "", "生活费", "还款", "聚餐AA", "代购"]
# 渠道 -> 转账方式 的搭配规则（transfer_type 枚举：扫码/网银/柜台）
CHANNEL_TYPE_MAP = {"微信": "扫码", "支付宝": "扫码", "银行转账": "网银", "现金": "柜台"}

# ---- 聊天参数 ----
CHAT_CHANNEL_WEIGHTS = {"微信": 70, "QQ": 20, "短信": 10}
MESSAGE_TYPE_WEIGHTS = {"文本": 85, "图片": 10, "语音": 5}
CHAT_TEMPLATES = ["在吗？", "明天几点到？", "收到。", "好的，没问题。", "老地方见哈。",
                  "今天忙不忙？", "改天一起吃饭。", "路上注意安全。", "行，到时候联系。", "照片我发你了。"]
MEDIA_DIR_NAME = "media"

# ---- 线索强度（mini 档降低强度但结构完整） ----
CLUE1_CALLS = {"mini": 8, "dev": 30, "bench": 30}    # 线索1：凌晨通话次数
CLUE1_AMOUNT = 8888.00                                # 线索1：大额转账
CLUE2_TEXTS = ["货准备好了吗？", "走一趟，老地方。", "晚上十点，别迟到。"]   # 线索2暗语
CLUE2_AMOUNT = 6666.00
CLUE3_TEXTS = ["货放城南仓库了。", "下午过去看看。"]                     # 线索3地点
