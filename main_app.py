import streamlit as st
import feedparser
import requests
import pandas as pd
from transformers import pipeline
from datetime import datetime, date

# --- 1. ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Gold AI Real-Time Pro", layout="wide", page_icon="🟡")

# --- 2. โหลด AI ---
@st.cache_resource
def load_sentiment_ai():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

analyzer = load_sentiment_ai()

# --- 3. ฟังก์ชันดึงข่าวล่าสุด (เน้นความสดใหม่) ---
def get_live_news():
    results = []
    today = date.today()
    
    # ดึงจาก Forex Factory (Calendar ข้อมูลจะแม่นยำและเป็นปัจจุบันที่สุด)
    try:
        # ดึงข้อมูล Calendar ของสัปดาห์นี้
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        ff_res = requests.get(ff_url, timeout=10)
        data = ff_res.json()
        
        for item in data:
            # แปลงเวลาจาก ISO (2026-02-26...)
            event_time = datetime.fromisoformat(item['date'])
            
            # คัดเฉพาะข่าวที่เกิดขึ้น "วันนี้" เท่านั้น
            if event_time.date() == today:
                analysis = analyzer(item['title'])[0]
                weight = 3 if item['impact'].lower() == 'high' else 2 if item['impact'].lower() == 'medium' else 1
                impact_icon = "🔴" if item['impact'].lower() == 'high' else "🟡" if item['impact'].lower() == 'medium' else "⚪"
                
                results.append({
                    "Time": event_time.strftime('%H:%M'),
                    "Currency": item['currency'],
                    "Headline": f"{impact_icon} {item['title']}",
                    "Impact": item['impact'].upper(),
                    "Sentiment": analysis['label'],
                    "Confidence": f"{analysis['score']:.2%}",
                    "Weight": weight
                })
    except Exception as e:
        st.error(f"Error fetching live data: {e}")
        
    return results

# --- 4. ตรรกะวิเคราะห์ทองคำ ---
def analyze_gold(news_list):
    gold_report = []
    for news in news_list:
        h_lower = news['Headline'].lower()
        # เน้นข่าว USD หรือข่าวที่กระทบทองโดยตรง
        if news['Currency'] == 'USD' or 'gold' in h_lower or 'fed' in h_lower:
            if news['Currency'] == 'USD':
                action = "📉 BEARISH (USD Strong)" if news['Sentiment'] == 'POSITIVE' else "🚀 BULLISH (USD Weak)"
            else:
                action = "🚀 BULLISH" if news['Sentiment'] == 'POSITIVE' else "📉 BEARISH"
            
            news['Gold_Action'] = action
            gold_report.append(news)
    return gold_report

# --- 5. Dashboard ---
st.title("🟡 Gold AI Specialist - TODAY'S LIVE")
st.subheader(f"📅 ประจำวันที่: {datetime.now().strftime('%d %B 2026')}")

if st.button('🔄 Update Live News Now'):
    st.cache_data.clear()

with st.spinner('กำลังดึงข้อมูลข่าวนาทีต่อนาที...'):
    today_news = get_live_news()
    gold_analysis = analyze_gold(today_news)

if today_news:
    # สรุป Bias วันนี้
    col1, col2, col3 = st.columns(3)
    bull_pts = sum(n['Weight'] for n in gold_analysis if "BULLISH" in n['Gold_Action'])
    bear_pts = sum(n['Weight'] for n in gold_analysis if "BEARISH" in n['Gold_Action'])
    
    col1.metric("Bullish Power", bull_pts)
    col2.metric("Bearish Power", bear_pts)
    with col3:
        if bull_pts > bear_pts: st.success("### AI Bias: BUY GOLD 🚀")
        elif bear_pts > bull_pts: st.error("### AI Bias: SELL GOLD 📉")
        else: st.warning("### AI Bias: NEUTRAL ⚖️")

    st.divider()
    
    # ตารางข่าววันนี้
    st.subheader("📊 Today's Gold Impact Events")
    if gold_analysis:
        st.dataframe(pd.DataFrame(gold_analysis)[['Time', 'Currency', 'Headline', 'Impact', 'Gold_Action']], use_container_width=True)
    else:
        st.info("วันนี้ยังไม่มีข่าว High Impact ที่กระทบทองคำโดยตรง")
        
    with st.expander("ดูตารางข่าวเศรษฐกิจทั้งหมดของวันนี้"):
        st.dataframe(pd.DataFrame(today_news), use_container_width=True)
else:
    st.warning("☕ ขณะนี้ยังไม่มีข่าวประกาศในตารางเวลาของวันนี้ กรุณารอข่าวรอบถัดไป")
