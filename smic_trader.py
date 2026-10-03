import yfinance as yf
import pandas as pd
import ta
import math

def check_smic_swing_signal():
    print("==========================================================")
    print(" 📡 981中芯國際 - 中短期波段 (1000股) 交易雷達")
    print("==========================================================")

    # 獲取 0981.HK 歷史數據 (半年)
    ticker = yf.Ticker("0981.HK")
    df = ticker.history(period="6mo")
    
    if df.empty:
        print("無法取得 0981.HK 數據，請檢查網絡或雅虎財經 API。")
        return

    # 計算技術指標
    # 1. 布林通道 (20MA, 2標準差)
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['BB_Upper'] = bb.bollinger_hband()
    df['BB_Lower'] = bb.bollinger_lband()
    df['BB_Mid'] = bb.bollinger_mavg()

    # 2. RSI (14日)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)

    # 3. MACD
    macd = ta.trend.MACD(df['Close'])
    df['MACD_Line'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff() # 柱狀圖

    # 取得最新一天的數據
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2]
    rsi = df['RSI'].iloc[-1]
    bb_lower = df['BB_Lower'].iloc[-1]
    bb_upper = df['BB_Upper'].iloc[-1]
    macd_hist = df['MACD_Hist'].iloc[-1]
    prev_macd_hist = df['MACD_Hist'].iloc[-2]

    capital_needed = current_price * 1000

    print(f" 現價: HKD \({current_price:.2f} | 預計單次投入 (2手/1000股): HKD\){capital_needed:,.2f}")
    print(f" RSI(14): {rsi:.1f} | 布林下軌: \({bb_lower:.2f} | 布林上軌:\){bb_upper:.2f}\n")

    # ==========================
    # 制定買賣邏輯
    # ==========================
    signal = "【WAIT】觀望中，持有現金或底倉不動。"
    action_color = "⚪"

    # 買入條件：股價接近或跌破布林下軌 AND RSI偏低 AND MACD動能未再惡化(綠柱縮短)
    is_price_low = current_price <= (bb_lower * 1.02) # 距離下軌 2% 以內
    is_rsi_oversold = rsi < 42
    is_macd_improving = macd_hist > prev_macd_hist # 動能改善

    # 賣出條件：股價接近布林上軌 OR RSI超買
    is_price_high = current_price >= (bb_upper * 0.98) # 距離上軌 2% 以內
    is_rsi_overbought = rsi > 65

    if is_price_low and is_rsi_oversold and is_macd_improving:
        signal = "【BUY】強烈買入訊號！符合高勝率超賣條件。"
        action_color = "🟢"
        print(f"{action_color} {signal}")
        print(f"   ▶ 建議動作：買入 1000 股。")
        print(f"   ▶ 防守設定：買入後若跌破 HKD ${(current_price * 0.94):.2f} (-6%)，無條件止蝕！")
        print(f"   ▶ 止賺目標：HKD ${(current_price * 1.10):.2f} (+10%)，或等待出現 SELL 訊號。")

    elif is_price_high or is_rsi_overbought:
        signal = "【SELL】強烈賣出/獲利了結訊號！"
        action_color = "🔴"
        print(f"{action_color} {signal}")
        print(f"   ▶ 建議動作：若持有波段倉位 (1000股)，請立即平倉套現。底倉保留不動。")
        
    else:
        print(f"{action_color} {signal}")
        if current_price < df['BB_Mid'].iloc[-1]:
            print("   ▶ 狀態：處於弱勢震盪區間，耐心等待跌至下軌。")
        else:
            print("   ▶ 狀態：處於強勢區間，持貨等待衝擊上軌。")

    print("==========================================================")

if __name__ == "__main__":
    check_smic_swing_signal()