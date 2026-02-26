import streamlit as st
import feedparser
import requests
import pandas as pd
import asyncio
from transformers import pipeline

# --- 1. ตั้งค่าพื้นฐาน (ป้องกันหน้าจอซ้ำ) ---
st.set_page_config(page_title="Pro Forex AI Hub", layout="wide")

# --- 2. โหลด AI แบบประหยัดพลังงาน (โหลดไวขึ้น) ---

@st.cache_resource
def load_ai():
    # ใช้โมเดลพื้นฐานที่เบาและเหมาะกับทรัพยากรบน Cloud
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# เรียกใช้งานฟังก์ชันที่ประกาศไว้ด้านบน
analyzer = load_ai()

# --- 3. ฟังก์ชันดึงข่าวจากหลายแหล่ง (รวม Forex Factory) ---
def get_forex_news():
    results = []
    
    # ดึงจาก Forex Factory (Economic Calendar)
    try:
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        ff_res = requests.get(ff_url, timeout=10)
        for item in ff_res.json()[:7]: # ดึง 7 ข่าวเด่น
            label = analyzer(item['title'])[0]
            results.append({
                "Source": "Forex Factory",
                "Currency": item['currency'],
                "Headline": item['title'],
                "Impact": item['impact'],
                "AI Sentiment": label['label'],
                "Confidence": f"{label['score']:.2%}"
            })
    except: pass

    # ดึงจาก Investing.com (RSS Feed)
    try:
        feed = feedparser.parse("https://www.investing.com/rss/news_285.rss")
        for entry in feed.entries[:5]:
            label = analyzer(entry.title)[0]
            results.append({
                "Source": "Investing.com",
                "Currency": "ALL",
                "Headline": entry.title,
                "Impact": "Medium/High",
                "AI Sentiment": label['label'],
                "Confidence": f"{label['score']:.2%}"
            })
    except: pass
    
    return results

# --- 4. การแสดงผล Dashboard ---
st.title("🌎 Pro Forex AI Intelligence Hub")
st.info("AI กำลังวิเคราะห์ข่าวเศรษฐกิจแบบ Real-time จากแหล่งข่าวชั้นนำ")

# ปุ่ม Refresh
if st.button('🔄 Sync Data & Re-analyze'):
    st.cache_data.clear()

# ประมวลผลและแสดงตาราง
with st.spinner('กำลังประมวลผลข้อมูล...'):
    news_data = get_forex_news()

if news_data:
    df = pd.DataFrame(news_data)
    
    # สรุปภาพรวม (Metrics)
    c1, c2, c3 = st.columns(3)
    pos_count = len(df[df['AI Sentiment'] == 'POSITIVE'])
    neg_count = len(df[df['AI Sentiment'] == 'NEGATIVE'])
    
    c1.metric("Bullish News 📈", pos_count)
    c2.metric("Bearish News 📉", neg_count)
    
    bias = "🚀 STRONG BUY" if pos_count > neg_count else "📉 STRONG SELL" if neg_count > pos_count else "⚖️ NEUTRAL"
    c3.subheader(f"Overall Bias: {bias}")

    st.divider()
    
    # แสดงตารางสวยงาม
    st.subheader("📊 รายละเอียดการวิเคราะห์รายข่าว")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("⚠️ ไม่พบข้อมูลข่าวในขณะนี้ กรุณารอสักครู่แล้วกด Refresh อีกครั้ง")


