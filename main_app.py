import streamlit as st
import feedparser
import requests
import pandas as pd
import asyncio
from transformers import pipeline
from telegram import Bot

# --- 1. ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Forex AI Intelligence Hub", layout="wide")

# --- 2. โหลด AI (ใช้ Cache เพื่อให้รันไวขึ้น) ---
@st.cache_resource
def load_ai():
    # ใช้โมเดลพื้นฐานที่โหลดไวและประมวลผลเร็วบน Cloud
    return pipeline("sentiment-analysis")

sentiment_pipeline = load_ai()

# --- 3. ฟังก์ชันดึงข่าว (Forex Factory + RSS) ---
def fetch_news():
    news_list = []
    # ดึงจาก Forex Factory (Calendar)
    try:
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        res_ff = requests.get(ff_url, timeout=10)
        for item in res_ff.json()[:5]:
            headline = f"[{item['currency']}] {item['title']}"
            analysis = sentiment_pipeline(item['title'])[0]
            news_list.append({
                "Source": "Forex Factory",
                "Headline": headline,
                "Label": analysis['label'],
                "Score": round(analysis['score'], 2)
            })
    except: pass
    
    # ดึงจาก Investing.com (RSS)
    try:
        feed = feedparser.parse("https://www.investing.com/rss/news_285.rss")
        for entry in feed.entries[:5]:
            analysis = sentiment_pipeline(entry.title)[0]
            news_list.append({
                "Source": "Investing.com",
                "Headline": entry.title,
                "Label": analysis['label'],
                "Score": round(analysis['score'], 2)
            })
    except: pass
    return news_list

# --- 4. ส่วนแสดงผล Dashboard (ไม่มีซ้ำแน่นอน) ---
st.title("🤖 Forex AI Intelligence Hub (24/7)")
st.write("ระบบวิเคราะห์ข่าวอัตโนมัติออนไลน์ 24 ชม.")

if st.button('🔄 Refresh Data Now'):
    st.cache_data.clear()

with st.spinner('AI กำลังวิเคราะห์ข่าวล่าสุด...'):
    data = fetch_news()

if data:
    df = pd.DataFrame(data)
    
    # ส่วน Metric สรุป
    c1, c2, c3 = st.columns(3)
    pos = len(df[df['Label'] == 'POSITIVE'])
    neg = len(df[df['Label'] == 'NEGATIVE'])
    
    c1.metric("Positive News", pos)
    c2.metric("Negative News", neg)
    
    bias = "BUY 📈" if pos > neg else "SELL 📉" if neg > pos else "NEUTRAL ⚖️"
    c3.metric("Market Bias", bias)

    st.divider()
    st.subheader("📊 Latest Market Analysis")
    # แสดงตาราง
    st.dataframe(df, use_container_width=True)
else:
    st.info("ℹ️ กำลังดึงข้อมูลข่าวใหม่... กรุณารอสักครู่หรือกด Refresh")
