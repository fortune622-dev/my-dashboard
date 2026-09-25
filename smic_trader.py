import json
import os
import pandas as pd
import yfinance as yf

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

# 1. 下載中芯國際 (0981.HK) 近期歷史數據
ticker = "0981.HK"
print(f"正在下載 {ticker} 最新數據...")
df = yf.download(ticker, period="6mo", interval="1d")
if isinstance(df.columns, pd.MultiIndex):
  df.columns = df.columns.get_level_values(0)


# 計算技術指標函數
def calculate_rsi(data, window=14):
  delta = data.diff()
  gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
  rs = gain / loss
  return 100 - (100 / (1 + rs))


df["RSI"] = calculate_rsi(df["Close"], 14)
df["MA20"] = df["Close"].rolling(window=20).mean()
df["STD20"] = df["Close"].rolling(window=20).std()
df["BB_Lower"] = df["MA20"] - (2 * df["STD20"])
df["BB_Middle"] = df["MA20"]  # 中軌作為動態止賺參考

latest = df.iloc[-1]
close_price = float(latest["Close"])
rsi_val = float(latest["RSI"])
bb_lower = float(latest["BB_Lower"])
bb_middle = float(latest["BB_Middle"])
volume = float(latest["Volume"])
avg_volume = float(df["Volume"].rolling(window=5).mean().iloc[-1])

print(f"今日收盤價: {close_price:.3f} | RSI: {rsi_val:.1f}\n")

# ==========================================
# 情況 A：檔案在「已買入」資料夾 -> 執行每日覆盤
# ==========================================
if has_position:
  buy_price = position["buy_price"]
  shares = position.get("shares", 1000)  # 預設 1000 股

  stop_loss = round(buy_price * 0.95, 3)
  fixed_tp = round(buy_price * 1.08, 3)
  dynamic_tp = round(bb_middle, 3)

  pnl_pct = ((close_price - buy_price) / buy_price) * 100

  print("--- 📊 中芯國際 (981) 【已買入】持倉覆盤報告 ---")
  print(f"持倉數量: {shares} 股 | 買入均價: ${buy_price}")
  print(f"今日收盤價: ${close_price:.3f} | 浮動盈虧: {pnl_pct:+.2f}%")
  print(
      f"🛑 止蝕價 (-5%): ${stop_loss} {'(⚠️ 警告：已跌破止蝕價！)' if close_price <= stop_loss else ''}"
  )
  print(f"🎯 固定止賺價 (+8%): ${fixed_tp}")
  print(
      f"📈 動態止賺價 (中軌): ${dynamic_tp} {'(🎯 提示：已達標動態止賺！)' if close_price >= dynamic_tp else ''}"
  )

# ==========================================
# 情況 B：檔案在「待買入」資料夾 -> 掃描買點
# ==========================================
else:
  print("--- 🔍 【待買入】正在掃描 3 大指標買入機會 ---")
  cond1 = close_price <= bb_lower
  cond2 = rsi_val <= 35
  cond3 = volume < avg_volume

  print(
      f"1. 價格觸及保利加下軌 (${bb_lower:.3f}): {'✅ 符合' if cond1 else '❌ 未符合'}"
  )
  print(f"2. RSI 超賣 (<=35): {'✅ 符合' if cond2 else '❌ 未符合'} ({rsi_val:.1f})")
  print(f"3. 縮量回調: {'✅ 符合' if cond3 else '❌ 未符合'}")

  if cond1 and cond2 and cond3:
    suggest_sl = round(close_price * 0.95, 3)
    suggest_tp = round(max(bb_middle, close_price * 1.08), 3)
    print("\n🚨 【發現買入訊號！】")
    print(f"建議買入 1000 股 | 參考價: ${close_price:.3f}")
    print(f"建議設定止蝕價: ${suggest_sl} (-5%)")
    print(f"建議設定止賺價: ${suggest_tp}")
  else:
    print("\n⏳ 今日未同時符合 3 大指標，繼續觀望。")