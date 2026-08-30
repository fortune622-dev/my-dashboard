import datetime
import os
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="私人資產與期權 Dashboard", page_icon="📈", layout="wide"
)

st.title("🚀 私人資產管理與期權策略 Dashboard")

tab1, tab2 = st.tabs(["🏛️ 939建銀 15年月供滾雪球", "📈 SPCX Sell Put 實時篩選"])

# ==========================================
# Tab 1: 939 建行月供進度
# ==========================================
with tab1:
    st.header("🏛️ 0939.HK 15 年月供雪球計劃")

    col1, col2, col3 = st.columns(3)

    try:
        ccb = yf.Ticker("0939.HK")
        live_price = ccb.fast_info["lastPrice"]
    except Exception:
        live_price = 8.5

    col1.metric("0939.HK 即時股價", f"${live_price:.2f} HKD")

    # 【重點修改】：加入 "939" 子資料夾路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file = os.path.join(current_dir, "939", "月供計劃-939建銀.xlsx")

    try:
        df = pd.read_excel(excel_file, sheet_name="定投", skiprows=8)
        valid_df = df.dropna(subset=["總股數"]).copy()

        if not valid_df.empty:
            latest = valid_df.iloc[-1]
            shares = latest["總股數"]
            invested = latest["累計投入總值\n(港幣)"]
            avg_cost = latest["平均價"]
            market_val = shares * live_price
            profit = market_val - invested

            col2.metric("累積持股量", f"{shares:,.0f} 股")
            col3.metric(
                "當前總市值",
                f"${market_val:,.2f} HKD",
                delta=f"${profit:,.2f} HKD",
            )

            st.divider()

            st.subheader("🏆 永動機成就解鎖進度")

            milestones = [
                (100000, "十萬大軍"),
                (250000, "鋼鐵防線"),
                (400000, "中產教父"),
                (600000, "終極永動機"),
                (800000, "自由之翼"),
                (1000000, "財務自由登頂"),
            ]

            for target, title in milestones:
                pct = min(1.0, shares / target)
                st.progress(
                    pct, text=f"{title} ({target:,.0f} 股) — 完成度: {pct*100:.1f}%"
                )

        else:
            st.warning("Excel 表格中尚未找到有效的持股記錄。")

    except Exception as e:
        st.warning(
            f"無法讀取『939/月供計劃-939建銀.xlsx』，請確認檔案已放置於 `939` 資料夾中。\n(完整路徑: `{excel_file}`)"
        )

# ==========================================
# Tab 2: SPCX Sell Put 實時篩選器
# ==========================================
with tab2:
    st.header("📈 SPCX 高性價比 Sell Put 實時掃描 (DTE 30-45天 & 勝率≥80%)")

    if st.button("🔍 一鍵開始掃描期權鏈", type="primary"):
        with st.spinner("正在連線抓取 SPCX 實時期權數據，請稍候..."):
            try:
                spcx = yf.Ticker("SPCX")
                try:
                    current_price = spcx.fast_info["lastPrice"]
                except Exception:
                    hist = spcx.history(period="1d")
                    current_price = hist["Close"].iloc[-1]

                st.write(f"**SPCX 當前現價：** `${current_price:.2f}`")

                expirations = spcx.options
                if not expirations:
                    st.error("未獲取到 SPCX 期權數據。")
                else:
                    results = []
                    today = datetime.date.today()

                    for exp_str in expirations:
                        exp_date = datetime.datetime.strptime(
                            exp_str, "%Y-%m-%d"
                        ).date()
                        dte = (exp_date - today).days

                        if dte < 30 or dte > 45:
                            continue

                        try:
                            opt_chain = spcx.option_chain(exp_str)
                            puts = opt_chain.puts
                        except Exception:
                            continue

                        for _, row in puts.iterrows():
                            strike = row["strike"]
                            bid = row.get("bid", 0)
                            ask = row.get("ask", 0)
                            open_interest = row.get("openInterest", 0)
                            volume = row.get("volume", 0)

                            if strike >= current_price or strike < (
                                current_price * 0.7
                            ):
                                continue
                            if bid <= 0:
                                continue
                            if (
                                open_interest is None or open_interest == 0
                            ) and (volume is None or volume == 0):
                                continue

                            if ask > 0 and (ask - bid) < (current_price * 0.1):
                                premium = (bid + ask) / 2
                            else:
                                premium = bid

                            if premium <= 0.05:
                                continue

                            delta = abs(row.get("delta", 0))
                            if delta == 0 or pd.isna(delta):
                                otm_pct = (
                                    current_price - strike
                                ) / current_price
                                win_rate = min(0.98, 0.5 + otm_pct * 2.5)
                            else:
                                win_rate = 1.0 - delta

                            if win_rate < 0.80:
                                continue

                            capital_required = strike * 100
                            breakeven_cost = strike - premium
                            annualized_return = (
                                (premium / strike) * (365 / dte) * 100
                            )
                            cp_score = (win_rate * 100) * annualized_return

                            results.append(
                                {
                                    "到期日": exp_str,
                                    "DTE(天)": dte,
                                    "行使價($)": strike,
                                    "現價差離": f"-{((current_price - strike)/current_price)*100:.1f}%",
                                    "預估期金": f"${premium:.2f}",
                                    "折算持股成本": f"${breakeven_cost:.2f}",
                                    "接股所需資金": f"${capital_required:,.0f}",
                                    "預估勝率": f"{win_rate*100:.1f}%",
                                    "年化回報": f"{annualized_return:.1f}%",
                                    "CP分數": round(cp_score, 1),
                                }
                            )

                    if results:
                        res_df = pd.DataFrame(results)
                        res_df = res_df.sort_values(
                            by="CP分數", ascending=False
                        ).reset_index(drop=True)
                        st.success(
                            f"掃描成功！為你找到 {len(res_df)} 隻符合條件的 Sell Put 合約。"
                        )
                        st.dataframe(res_df.head(10), use_container_width=True)
                    else:
                        st.info(
                            "目前在 DTE 30-45 天內沒有符合條件的合約（非開市時段可能無報價數據）。"
                        )

            except Exception as e:
                st.error(f"連線或計算時發生錯誤: {e}")