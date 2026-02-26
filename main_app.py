import streamlit as st
import feedparser
import requests
import pandas as pd
from transformers import pipeline
from datetime import datetime

# --- 1. ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Gold AI Pro Hub", layout="wide", page_icon="🟡")

# --- 2. โหลด AI แบบประหยัดพลังงาน ---
@st.cache_resource
def load_sentiment_ai():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

analyzer = load_sentiment_ai()

# --- 3. ฟังก์ชันดึงข่าวพร้อมเวลา (Release Time) ---
def get_advanced_news():
    results = []
    # ดึงจาก Forex Factory (Economic Calendar)
    try:
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        ff_res = requests.get(ff_url, timeout=10)
        for item in ff_res.json()[:15]: 
            analysis = analyzer(item['title'])[0]
            weight = 3 if item['impact'].lower() == 'high' else 2 if item['impact'].lower() == 'medium' else 1
            impact_icon = "🔴" if item['impact'].lower() == 'high' else "🟡" if item['impact'].lower() == 'medium' else "⚪"
            
            # จัดรูปแบบเวลา (Forex Factory ให้มาเป็น ISO format)
            raw_time = item['date'] # ตัวอย่าง: 2026-02-26T10:30:00-05:00
            formatted_time = raw_time.replace('T', ' ').split('-')[0] # ตัดให้ดูง่าย
            
            results.append({
                "Time": formatted_time,
                "Source": "Forex Factory",
                "Currency": item['currency'],
                "Headline": f"{impact_icon} {item['title']}",
                "Impact": item['impact'].upper(),
                "AI Sentiment": analysis['label'],
                "Confidence": f"{analysis['score']:.2%}",
                "Weight": weight,
                "Raw_Score": analysis['score']
            })
    except: pass

    # ดึงจาก Investing.com (RSS Feed)
    try:
        feed = feedparser.parse("https://www.investing.com/rss/news_285.rss")
        for entry in feed.entries[:5]:
            analysis = analyzer(entry.title)[0]
            # เวลาจาก RSS
            pub_time = entry.get('published', 'N/A')
            
            results.append({
                "Time": pub_time,
                "Source": "Investing.com",
                "Currency": "ALL",
                "Headline": f"🌐 {entry.title}",
                "Impact": "MEDIUM",
                "AI Sentiment": analysis['label'],
                "Confidence": f"{analysis['score']:.2%}",
                "Weight": 1,
                "Raw_Score": analysis['score']
            })
    except: pass
    
    return results

# --- 4. ตรรกะวิเคราะห์เจาะจงทองคำ (XAU/USD) ---
def analyze_gold_impact(news_list):
    gold_report = []
    keywords = ['gold', 'xau', 'fed', 'inflation', 'usd', 'cpi', 'interest rate', 'fomc', 'nfp']
    
    for news in news_list:
        h_lower = news['Headline'].lower()
        if any(k in h_lower for k in keywords) or news['Currency'] == 'USD':
            if news['Currency'] == 'USD':
                if news['AI Sentiment'] == 'POSITIVE':
                    action = "📉 BEARISH (USD Strong)"
                else:
                    action = "🚀 BULLISH (USD Weak)"
            else:
                action = "🚀 BULLISH" if news['AI Sentiment'] == 'POSITIVE' else "📉 BEARISH"
            
            news['Gold_Action'] = action
            gold_report.append(news)
    return gold_report

# --- 5. การแสดงผล Dashboard ---
st.title("🟡 Gold AI Specialist - Real-time Analysis")
st.write(f"อัปเดตข้อมูลล่าสุดเมื่อ: {datetime.now().strftime('%H:%M:%S')}")

if st.button('🔄 Refresh & Sync Latest News'):
    st.cache_data.clear()

with st.spinner('AI กำลังตรวจสอบเวลาข่าวและวิเคราะห์ตลาด...'):
    news_data = get_advanced_news()
    gold_news = analyze_gold_impact(news_data)

if news_data:
    df = pd.DataFrame(news_data)
    
    # --- ส่วนที่ 1: สรุปกลยุทธ์ทองคำ ---
    st.header("✨ XAU/USD Strategy Board")
    g_col1, g_col2, g_col3 = st.columns(3)
    
    bull_pts = sum(n['Weight'] for n in gold_news if "BULLISH" in n['Gold_Action'])
    bear_pts = sum(n['Weight'] for n in gold_news if "BEARISH" in n['Gold_Action'])
    
    g_col1.metric("Bullish Power", bull_pts)
    g_col2.metric("Bearish Power", bear_pts)
    
    with g_col3:
        if bull_pts > bear_pts:
            st.success("### AI Bias: BUY GOLD 🚀")
        elif bear_pts > bull_pts:
            st.error("### AI Bias: SELL GOLD 📉")
        else:
            st.warning("### AI Bias: NEUTRAL ⚖️")

    # ตารางข่าวทองคำ (โชว์เวลาด้วย)
    st.subheader("📊 Gold Analysis with Release Time")
    if gold_news:
        st.dataframe(pd.DataFrame(gold_news)[['Time', 'Headline', 'Impact', 'Gold_Action']], use_container_width=True)

    st.divider()

    # --- ส่วนที่ 2: ข่าวทั้งหมด ---
    st.header("🌎 Global Market Overview")
    st.dataframe(df[['Time', 'Source', 'Currency', 'Headline', 'Impact', 'AI Sentiment', 'Confidence']], use_container_width=True)

else:
    st.warning("⚠️ ไม่พบข้อมูลข่าว กรุณากดปุ่ม Refresh")
