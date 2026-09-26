import json
import os
import pandas as pd
import yfinance as yf

# 自動確保雲端上有這兩個資料夾
os.makedirs("待買入", exist_ok=True)
os.makedirs("已買入", exist_ok=True)

# 資料夾路徑定義
PENDING_PATH = "待買入/position_status.json"
ACTIVE_PATH = "已買入/position_status.json"

# 自動判斷模式：如果檔案在「已買入」才算已持倉；在「待買入」一律當作未持倉掃描
if os.path.exists(ACTIVE_PATH):
  with open(ACTIVE_PATH, "r", encoding="utf-8") as f:
    position = json.load(f)
  has_position = True
else:
  has_position = False
