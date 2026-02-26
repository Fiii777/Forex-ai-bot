import streamlit as st
import feedparser
import requests
import pandas as pd
from transformers import pipeline
from datetime import datetime, date

# --- 1. ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Gold AI Live 2026", layout="wide", page_icon="🟡")

# --- 2. โหลด AI ---
@st.cache_resource
def load_sentiment_ai():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

analyzer = load_sentiment_ai()

# --- 3. ฟังก์ชันดึงข่าวล่าสุด (พร้อมระบบสำรอง) ---
def get_live_news_v2():
    results = []
    today_str = date.today().strftime('%Y-%m-%d')
    
    # แหล่งที่ 1: Forex Factory (ปฏิทินเศรษฐกิจ)
    try:
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        ff_res = requests.get(ff_url, timeout=5)
        if ff_res.status_code == 200:
            for item in ff_res.json():
                if today_str in item['date']:
                    analysis = analyzer(item['title'])[0]
                    results.append({
                        "Time": item['date'].split('T')[1][:5],
                        "Currency": item['currency'],
                        "Headline": f"🔴 {item['title']}" if item['impact'] == 'High' else f"⚪ {item['title']}",
                        "Source": "Forex Factory",
                        "Sentiment": analysis['label'],
                        "Score": analysis['score']
                    })
    except:
        pass # ถ้าล่มให้ข้ามไปแหล่งที่ 2

    # แหล่งที่ 2: FXStreet (สดและไวกว่า) - ดึงผ่าน RSS ที่มักจะไม่โดนบล็อก
    try:
        fx_feed = feedparser.parse("https://www.fxstreet.com/rss/news")
        for entry in fx_feed.entries[:10]:
            # กรองเฉพาะข่าวที่มีคำว่า Gold, Fed, USD และเป็นของวันนี้
            h_lower = entry.title.lower()
            if any(k in h_lower for k in ['gold', 'xau', 'fed', 'usd', 'inflation']):
                analysis = analyzer(entry.title)[0]
                results.append({
                    "Time": "LIVE",
                    "Currency": "XAU/USD",
                    "Headline": f"🔥 {entry.title}",
                    "Source": "FXStreet Live",
                    "Sentiment": analysis['label'],
                    "Score": analysis['score']
                })
    except:
        pass

    return results

# --- 4. Dashboard ---
st.title("🟡 Gold AI Specialist - TODAY'S LIVE 2026")
st.subheader(f"📅 ข้อมูลประจำวันที่: {datetime.now().strftime('%d %B 2026')}")

if st.button('🔄 Update Live News Now'):
    st.cache_data.clear()

with st.spinner('กำลังดึงข่าวสดวินาทีต่อวินาที...'):
    news_list = get_live_news_v2()

if news_list:
    df = pd.DataFrame(news_list)
    
    # วิเคราะห์ทองคำ
    st.header("✨ Today's Gold Impact Strategy")
    
    # คำนวณ Power
    bull_power = len(df[df['Sentiment'] == 'POSITIVE'])
    bear_power = len(df[df['Sentiment'] == 'NEGATIVE'])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Bullish News", bull_power)
    c2.metric("Bearish News", bear_power)
    
    with c3:
        if bull_power > bear_power: st.success("🚀 BIAS: BUY GOLD")
        elif bear_power > bull_power: st.error("📉 BIAS: SELL GOLD")
        else: st.warning("⚖️ BIAS: NEUTRAL")

    st.divider()
    
    # แสดงตารางข่าวที่สดที่สุด
    st.subheader("📊 Live News Feed (Filtered for Gold & USD)")
    st.dataframe(df[['Time', 'Source', 'Headline', 'Sentiment']], use_container_width=True)
else:
    st.warning("⚠️ ไม่สามารถเชื่อมต่อแหล่งข่าวได้ชั่วคราว หรือยังไม่มีข่าวสำคัญในชั่วโมงนี้")
    st.info("คำแนะนำ: ตรวจสอบการเชื่อมต่ออินเทอร์เน็ตของ Server หรือลองกด Update อีกครั้งใน 1 นาที")
