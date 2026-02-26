import streamlit as st
import feedparser
import requests
import pandas as pd
import asyncio
from transformers import pipeline

# --- 1. ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Gold AI Specialist Hub", layout="wide", page_icon="🟡")

# --- 2. โหลด AI แบบประหยัดพลังงาน ---
@st.cache_resource
def load_sentiment_ai():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

analyzer = load_sentiment_ai()

# --- 3. ฟังก์ชันดึงข่าวและวิเคราะห์ผลกระทบ ---
def get_advanced_forex_news():
    results = []
    # ดึงจาก Forex Factory
    try:
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        ff_res = requests.get(ff_url, timeout=10)
        for item in ff_res.json()[:10]:
            label = analyzer(item['title'])[0]
            # ให้คะแนนตาม Impact
            weight = 3 if item['impact'].lower() == 'high' else 2 if item['impact'].lower() == 'medium' else 1
            
            results.append({
                "Source": "Forex Factory",
                "Currency": item['currency'],
                "Headline": item['title'],
                "Impact": item['impact'],
                "Sentiment": label['label'],
                "Weight": weight,
                "Score": label['score']
            })
    except: pass
    return results

# --- 4. ส่วนวิเคราะห์ทองคำ (XAU/USD) ---
def analyze_gold_impact(news_data):
    gold_analysis = []
    keywords = ['gold', 'xau', 'fed', 'inflation', 'usd', 'fomc', 'interest rate', 'cpi']
    
    for news in news_data:
        h_lower = news['Headline'].lower()
        if any(key in h_lower for key in keywords) or news['Currency'] in ['USD', 'XAU']:
            # Logic: ทองคำมักสวนทางกับ USD
            if news['Currency'] == 'USD':
                if news['Sentiment'] == 'POSITIVE':
                    g_signal = "📉 BEARISH (USD Strong)"
                    g_color = "red"
                else:
                    g_signal = "🚀 BULLISH (USD Weak)"
                    g_color = "green"
            else:
                g_signal = "🚀 BULLISH" if news['Sentiment'] == 'POSITIVE' else "📉 BEARISH"
                g_color = "green" if news['Sentiment'] == 'POSITIVE' else "red"
            
            news['Gold_Signal'] = g_signal
            news['Signal_Color'] = g_color
            gold_analysis.append(news)
    return gold_analysis

# --- 5. หน้า Dashboard ---
st.title("🟡 Gold AI Specialist & Forex Intelligence")
st.markdown("ระบบวิเคราะห์ Sentiment เจาะลึก **ทองคำ (XAU/USD)** และข่าวเศรษฐกิจโลก")

if st.button('🔄 Sync & Re-Analyze Data'):
    st.cache_data.clear()

with st.spinner('AI กำลังวิเคราะห์ผลกระทบต่อราคาทองคำ...'):
    all_news = get_advanced_forex_news()
    gold_news = analyze_gold_impact(all_news)

if all_news:
    # --- ส่วนสรุปทองคำ ---
    st.subheader("✨ Gold Strategy (XAU/USD Focus)")
    g_col1, g_col2 = st.columns(2)
    
    bullish_pts = sum(n['Weight'] for n in gold_news if "BULLISH" in n['Gold_Signal'])
    bearish_pts = sum(n['Weight'] for n in gold_news if "BEARISH" in n['Gold_Signal'])
    
    g_col1.metric("Gold Bullish Power (Weighted)", bullish_pts)
    g_col2.metric("Gold Bearish Power (Weighted)", bearish_pts)
    
    if bullish_pts > bearish_pts:
        st.success("### 🚀 Overall Gold Bias: BUY / LONG")
    elif bearish_pts > bullish_pts:
        st.error("### 📉 Overall Gold Bias: SELL / SHORT")
    else:
        st.warning("### ⚖️ Overall Gold Bias: SIDEWAYS / NEUTRAL")

    st.divider()

    # --- ตารางวิเคราะห์ทองคำ ---
    st.subheader("📊 Gold Focused Analysis")
    gold_df = pd.DataFrame(gold_news)
    if not gold_df.empty:
        st.dataframe(gold_df[['Currency', 'Headline', 'Impact', 'Gold_Signal']], use_container_width=True)

    # --- ตารางข่าวทั้งหมด ---
    with st.expander("ดูข่าวเศรษฐกิจทั้งหมด"):
        st.dataframe(pd.DataFrame(all_news), use_container_width=True)
else:
    st.warning("⚠️ กำลังรอข้อมูลข่าวล่าสุด...")
