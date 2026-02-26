import streamlit as st
import feedparser
import requests
import pandas as pd
from transformers import pipeline

# --- 1. ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Gold AI Specialist Hub", layout="wide", page_icon="🟡")

# --- 2. โหลด AI แบบประหยัดพลังงาน (DistilBERT) ---
@st.cache_resource
def load_sentiment_ai():
    # ใช้โมเดลที่เบาและเหมาะกับการรันบน Streamlit Cloud
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

analyzer = load_sentiment_ai()

# --- 3. ฟังก์ชันดึงข่าวและวิเคราะห์น้ำหนัก (Impact Weighting) ---
def get_advanced_news():
    results = []
    # ดึงข้อมูลปฏิทินเศรษฐกิจจาก Forex Factory
    try:
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        ff_res = requests.get(ff_url, timeout=10)
        for item in ff_res.json()[:15]: # ดึง 15 ข่าวล่าสุด
            analysis = analyzer(item['title'])[0]
            # กำหนดน้ำหนักตามความแรงของข่าว
            weight = 3 if item['impact'].lower() == 'high' else 2 if item['impact'].lower() == 'medium' else 1
            
            results.append({
                "Source": "Forex Factory",
                "Currency": item['currency'],
                "Headline": item['title'],
                "Impact": item['impact'],
                "Sentiment": analysis['label'],
                "Weight": weight
            })
    except: pass
    return results

# --- 4. ตรรกะวิเคราะห์ผลกระทบต่อทองคำ (XAU/USD Logic) ---
def analyze_gold_impact(news_list):
    gold_report = []
    # คำสำคัญที่มีผลต่อราคาทองคำ
    keywords = ['gold', 'xau', 'fed', 'inflation', 'usd', 'cpi', 'interest rate']
    
    for news in news_list:
        h_lower = news['Headline'].lower()
        if any(k in h_lower for k in keywords) or news['Currency'] == 'USD':
            # ความสัมพันธ์แบบสวนทาง: ถ้าดอลลาร์บวก ทองคำมักลบ
            if news['Currency'] == 'USD' and news['Sentiment'] == 'POSITIVE':
                signal = "📉 BEARISH (USD Strong)"
            elif news['Currency'] == 'USD' and news['Sentiment'] == 'NEGATIVE':
                signal = "🚀 BULLISH (USD Weak)"
            else:
                signal = "🚀 BULLISH" if news['Sentiment'] == 'POSITIVE' else "📉 BEARISH"
            
            news['Gold_Action'] = signal
            gold_report.append(news)
    return gold_report

# --- 5. การแสดงผล Dashboard ---
st.title("🟡 Gold AI Specialist & Forex Intelligence")
st.write("วิเคราะห์ Sentiment เจาะลึกทองคำ (XAU/USD) และข่าวเศรษฐกิจโลก")

if st.button('🔄 Sync & Re-Analyze Gold Market'):
    st.cache_data.clear()

with st.spinner('AI กำลังวิเคราะห์ผลกระทบต่อราคาทองคำ...'):
    all_data = get_advanced_news()
    gold_data = analyze_gold_impact(all_data)

if all_data:
    # --- ส่วนสรุปสำหรับเทรดเดอร์ทอง ---
    st.subheader("✨ Gold Trading Strategy (XAU/USD Focus)")
    col1, col2, col3 = st.columns(3)
    
    bullish_pts = sum(n['Weight'] for n in gold_data if "BULLISH" in n['Gold_Action'])
    bearish_pts = sum(n['Weight'] for n in gold_data if "BEARISH" in n['Gold_Action'])
    
    col1.metric("Bullish Power (Weight)", bullish_pts)
    col2.metric("Bearish Power (Weight)", bearish_pts)
    
    with col3:
        if bullish_pts > bearish_pts:
            st.success("### Overall: BUY GOLD 🚀")
        elif bearish_pts > bullish_pts:
            st.error("### Overall: SELL GOLD 📉")
        else:
            st.warning("### Overall: SIDEWAYS ⚖️")

    st.divider()

    # --- แสดงตารางเจาะลึกทองคำ ---
    st.subheader("📊 Gold Analysis Details")
    if gold_data:
        st.dataframe(pd.DataFrame(gold_data)[['Currency', 'Headline', 'Impact', 'Gold_Action']], use_container_width=True)
    
    # --- แสดงข่าวทั้งหมด ---
    with st.expander("ดูข่าวเศรษฐกิจโลกทั้งหมด (Forex Factory)"):
        st.dataframe(pd.DataFrame(all_data), use_container_width=True)
else:
    st.info("ℹ️ กำลังรอข้อมูลข่าวใหม่... กรุณากด Refresh")
