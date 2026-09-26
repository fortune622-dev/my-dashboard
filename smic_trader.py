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

print("========================================")
print("  中芯國際 (0981.HK) 量化監控系統啟動")
print("========================================")

# 自動判斷模式：如果檔案在「已買入」才算持倉；在「待買入」一律當作未持倉掃描
if os.path.exists(ACTIVE_PATH):
    with open(ACTIVE_PATH, "r", encoding="utf-8") as f:
        position = json.load(f)
    print("【目前模式】已持倉覆盤模式")
    print(f"持倉資料：{position}")
    
    # 這裡未來會接續您的覆盤計算邏輯
    # buy_price = position.get("buy_price", 0)
    # print(f"買入價: {buy_price}")

else:
    print("【目前模式】未持倉尋找買點模式")
    print("正在雲端背景掃描 3 大指標（保利加下軌、RSI 超賣、縮量回調）...")
    
    # 測試抓取中芯國際數據
    ticker = "0981.HK"
    df = yf.download(ticker, period="60d", interval="1d", progress=False)
    if not df.empty:
        current_price = float(df['Close'].iloc[-1])
        print(f"最新抓取中芯國際 ({ticker}) 收盤價: {current_price:.3f}")
    else:
        print("警告：暫時無法取得最新行情數據。")

print("========================================")
print("  今日檢查執行完畢")
print("========================================")
