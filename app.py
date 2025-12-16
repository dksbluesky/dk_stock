import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. 頁面設定 ---
st.set_page_config(page_title="支撐壓力戰情室", page_icon="🛡️", layout="centered")

# --- 2. 樣式 (強化紅綠視覺) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .metric-card { background-color: #262730; padding: 15px; border-radius: 10px; border-left: 5px solid #4e8cff; margin-bottom: 10px; }
    .support-card { background-color: #1c2e2e; padding: 10px; border-radius: 8px; border: 1px solid #00c853; text-align: center; }
    .resist-card { background-color: #2e1c1c; padding: 10px; border-radius: 8px; border: 1px solid #ff4b4b; text-align: center; }
    h1, h2, h3 { color: #facc15 !important; font-family: 'Helvetica', sans-serif; }
    [data-testid="stMetricLabel"] { color: #aaaaaa !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ 支撐壓力戰情室")
st.caption("無 OBI 替代方案：VWAP 成本線 + CDP 關卡")

col1, col2 = st.columns([3, 1])
with col1:
    symbol_input = st.text_input("輸入代號", value="2330.TW", placeholder="例: 2330.TW")
with col2:
    st.write("") 
    st.write("") 
    run_btn = st.button("計算")

# --- 3. 核心運算 (CDP & VWAP) ---
def analyze_support(symbol):
    try:
        stock = yf.Ticker(symbol)
        
        # A. 抓取日線數據 (為了算 CDP - 需要昨天的 High/Low/Close)
        df_daily = stock.history(period="5d")
        if df_daily.empty:
            st.error("❌ 抓取失敗，請確認代號。")
            return
            
        # 取得昨天數據 (倒數第二筆，因為最後一筆是今天盤中)
        # 如果今天是開盤第一天，最後一筆就是今天，前一筆就是昨天
        if len(df_daily) < 2:
            st.warning("數據不足無法計算 CDP")
            return
            
        yesterday = df_daily.iloc[-2]
        y_high = yesterday['High']
        y_low = yesterday['Low']
        y_close = yesterday['Close']
        
        # CDP 公式計算
        cdp = (y_high + y_low + (2 * y_close)) / 4
        ah = cdp + (y_high - y_low) # 最高壓力 (追買點)
        nh = (2 * cdp) - y_low      # 賣出點 (壓力)
        nl = (2 * cdp) - y_high     # 買進點 (支撐)
        al = cdp - (y_high - y_low) # 最低支撐 (停損點)

        # B. 抓取分鐘數據 (為了算 VWAP - 即時成本)
        df_1m = stock.history(period="1d", interval="1m")
        if df_1m.empty:
            # 盤後或抓不到分鐘線，用日線頂替顯示現價，但 VWAP 會失效
            current_price = df_daily['Close'].iloc[-1]
            vwap = current_price # 暫代
            has_intraday = False
        else:
            current_price = df_1m['Close'].iloc[-1]
            # VWAP 計算: 累積成交金額 / 累積成交量
            df_1m['Typical_Price'] = (df_1m['High'] + df_1m['Low'] + df_1m['Close']) / 3
            df_1m['TP_V'] = df_1m['Typical_Price'] * df_1m['Volume']
            vwap = df_1m['TP_V'].cumsum() / df_1m['Volume'].cumsum()
            vwap = vwap.iloc[-1]
            has_intraday = True

        # 計算漲跌
        prev_close = df_daily['Close'].iloc[-2]
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        # --- 4. 畫面顯示 ---

        # 頂部價格卡片
        color_val = '#ff4b4b' if change_pct > 0 else '#00c853'
        st.markdown(f"""
        <div class="metric-card">
            <p style='margin:0; color: #aaa;'>即時股價</p>
            <h2 style='margin:0; color: white;'>{current_price:.2f} <span style='font-size:18px; color:{color_val}'>{change_pct:+.2f}%</span></h2>
        </div>
        """, unsafe_allow_html=True)

        # 戰術分析：現在在哪裡？
        st.markdown("### 🧭 戰場定位")
        
        # 判斷 VWAP 支撐
        if current_price >= vwap:
            vwap_status = "股價在成本之上 (支撐強)"
            vwap_color = "normal" # 綠/紅
        else:
            vwap_status = "股價在成本之下 (壓力重)"
            vwap_color = "inverse" # 反白警告

        st.metric("VWAP 當沖成本線", f"{vwap:.2f}", vwap_status, delta_color="normal")
        if not has_intraday:
            st.info("⚠️ 目前無盤中即時成交明細，VWAP 為估算值。")

        # CDP 棋盤
        st.markdown("### 🧱 CDP 攻防關卡 (預判)")
        st.write("這是根據昨日波動算出的今日防線，主力常在此佈局。")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div class='resist-card'>🔴 壓力二 (追買)<br><b>{ah:.2f}</b></div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"<div class='resist-card'>🟠 壓力一 (賣出)<br><b>{nh:.2f}</b></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='support-card'>🟢 支撐一 (買進)<br><b>{nl:.2f}</b></div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"<div class='support-card'>🔵 支撐二 (停損)<br><b>{al:.2f}</b></div>", unsafe_allow_html=True)

        # 軍師總結
        pos = "觀望"
        if current_price > nh: pos = "強勢突破壓力，小心假突破"
        elif current_price < nl: pos = "跌破第一支撐，尋求第二防線"
        elif nl <= current_price <= nh: pos = "區間震盪，低買高賣"
        
        st.info(f"💡 軍師戰略：{pos}。若股價回測 {nl:.2f} 不破且 VWAP 向上，為最佳買點。")

    except Exception as e:
        st.error(f"分析失敗：{e}")

if run_btn or symbol_input:
    analyze_support(symbol_input.upper().strip())
