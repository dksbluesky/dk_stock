import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import datetime

# --- 頁面設定 (手機優先模式) ---
st.set_page_config(page_title="首席金融軍師", page_icon="♟️", layout="centered")

# --- 自定義 CSS (暗黑戰術風格) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .metric-card { background-color: #262730; padding: 15px; border-radius: 10px; border-left: 5px solid #4e8cff; margin-bottom: 10px; }
    .risk-card { background-color: #262730; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 10px; }
    .advice-card { background-color: #1c2e4a; padding: 15px; border-radius: 10px; border: 1px solid #4e8cff; margin-bottom: 10px; }
    h1, h2, h3 { color: #4e8cff !important; font-family: 'Helvetica', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# --- 標題區 ---
st.title("♟️ 首席金融軍師")
st.caption("行動決策儀表板 | 即時戰況分析")

# --- 輸入區 ---
col1, col2 = st.columns([3, 1])
with col1:
    symbol_input = st.text_input("輸入代號", value="2330.TW", placeholder="例如: 2330.TW, NVDA")
with col2:
    st.write("") # Spacer
    st.write("") 
    run_btn = st.button("分析")

# --- 核心邏輯函數 ---
def analyze_stock(symbol):
    try:
        # 1. 獲取數據
        stock = yf.Ticker(symbol)
        df = stock.history(period="6mo")
        
        if df.empty:
            st.error("❌ 查無此股票數據，請確認代號 (台股請加 .TW)")
            return

        # 2. 計算指標
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change_pct = ((current_price - prev_price) / prev_price) * 100
        
        # 移動平均線 (SMA)
        df['SMA20'] = ta.sma(df['Close'], length=20)
        df['SMA60'] = ta.sma(df['Close'], length=60)
        
        # RSI
        df['RSI'] = ta.rsi(df['Close'], length=14)
        current_rsi = df['RSI'].iloc[-1]
        
        # 乖離率 (Bias)
        bias_20 = ((current_price - df['SMA20'].iloc[-1]) / df['SMA20'].iloc[-1]) * 100

        # 3. 戰場現況判斷
        trend = "盤整震盪"
        trend_color = "off"
        if current_price > df['SMA20'].iloc[-1] > df['SMA60'].iloc[-1]:
            trend = "多頭排列 (強勢)"
            trend_color = "up"
        elif current_price < df['SMA20'].iloc[-1] < df['SMA60'].iloc[-1]:
            trend = "空頭排列 (弱勢)"
            trend_color = "down"
        elif current_price > df['SMA20'].iloc[-1]:
            trend = "短多格局 (站上月線)"
            trend_color = "up"
            
        # 4. 軍師建議生成 logic
        advice_long = ""
        advice_short = ""
        summary = ""
        
        # 根據 RSI 判斷
        if current_rsi > 70:
            advice_short = "短線過熱，隨時可能回檔，切勿追高。"
            summary = "「 居高思危，獲利入袋 」"
        elif current_rsi < 30:
            advice_short = "乖離過大，醞釀跌深反彈，可嘗試搶短。"
            summary = "「 靜待落底，分批承接 」"
        else:
            advice_short = "區間操作，沿五日線操作。"
            summary = "「 順勢而為，步步為營 」"

        if trend_color == "up":
            advice_long = "多頭架構未破，沿月線續抱。"
            if summary == "": summary = "「 乘勝追擊，擴大戰果 」"
        elif trend_color == "down":
            advice_long = "空方勢力強，不宜長期持有，反彈減碼。"
            if summary == "": summary = "「 保留現金，等待黎明 」"
        else:
            advice_long = "方向未明，多看少做。"

        # --- 顯示儀表板 (UI) ---
        
        # A. 戰場現況 (Header Card)
        st.markdown("### 1. 戰場現況")
        color_code = "🟢" if change_pct < 0 else "🔴" # 台股紅漲綠跌
        st.markdown(f"""
        <div class="metric-card">
            <h2 style='margin:0; color: white;'>{current_price:.2f} <span style='font-size:16px; color:{'#ff4b4b' if change_pct > 0 else '#00c853'}'>{change_pct:+.2f}%</span></h2>
            <p style='margin:0; color: #aaaaaa; font-weight:bold;'>{trend}</p>
        </div>
        """, unsafe_allow_html=True)

        # B. 關鍵數據表
        st.markdown("### 2. 關鍵數據")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("RSI 強弱指標", f"{current_rsi:.1f}", delta="過熱" if current_rsi>70 else "超賣" if current_rsi<30 else "中性", delta_color="inverse")
        with c2:
            st.metric("月線乖離", f"{bias_20:.1f}%", help="正值代表股價高於月線")
            
        # 支撐壓力 (簡單演算法: 近20日最高/最低)
        support = df['Low'].tail(20).min()
        pressure = df['High'].tail(20).max()
        
        st.dataframe(pd.DataFrame({
            "指標": ["短期支撐", "短期壓力", "成交量"],
            "數值": [f"{support:.2f}", f"{pressure:.2f}", f"{df['Volume'].iloc[-1]/1000:.0f} 張"]
        }), hide_index=True, use_container_width=True)

        # C. 風險雷達
        st.markdown("### 3. 風險雷達")
        risk_text = []
        if current_rsi > 75: risk_text.append("⚠️ 技術面嚴重過熱")
        if bias_20 > 10: risk_text.append("⚠️ 乖離過大，慎防拉回")
        if change_pct < -3: risk_text.append("⚠️ 單日重挫，空方力道強")
        if not risk_text: risk_text.append("✅ 目前技術面無顯著極端風險")
        
        for risk in risk_text:
            st.markdown(f"<div class='risk-card'>{risk}</div>", unsafe_allow_html=True)

        # D. 軍師建議
        st.markdown("### 4. 軍師建議")
        st.markdown(f"""
        <div class="advice-card">
            <strong style="color:#aaa">🗓 長期策略：</strong><br>{advice_long}<br><br>
            <strong style="color:#aaa">⚡ 短線策略：</strong><br>{advice_short}
            <hr style="border-color:#333">
            <div style="text-align:center; font-size: 1.2em; font-weight:bold; color:#4e8cff;">
                {summary}
            </div>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"分析失敗：{e}")

# 執行分析
if run_btn or symbol_input:
    analyze_stock(symbol_input.upper())