import streamlit as st
import feedparser
import requests
import pandas as pd
from transformers import pipeline
from datetime import datetime, date

# --- 1. การตั้งค่าหน้าจอและ UI Theme ---
st.set_page_config(page_title="Gold AI Expert Specialist", layout="wide", page_icon="🏦")

# --- 2. โหลด AI Sentiment (DistilBERT) ---
@st.cache_resource
def load_sentiment_ai():
    # ใช้โมเดลที่เสถียรสำหรับการวิเคราะห์ข่าวเศรษฐกิจ
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

analyzer = load_sentiment_ai()

# --- 3. ฟังก์ชันดึงข่าวล่าสุด (เพิ่มระบบจัดการ Error และแหล่งข่าวสำรอง) ---
def get_live_expert_news():
    results = []
    today_str = date.today().strftime('%Y-%m-%d')
    
    # พยายามดึงข้อมูลจาก Forex Factory (Calendar)
    try:
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        # เพิ่ม timeout เพื่อป้องกันหน้าจอค้างนานเกินไป
        ff_res = requests.get(ff_url, timeout=5) 
        if ff_res.status_code == 200:
            for item in ff_res.json():
                # กรองเฉพาะข่าวของ "วันนี้" ในปี 2026
                if today_str in item['date']:
                    label = analyzer(item['title'])[0]
                    impact = item['impact'].lower()
                    v_score = "🔴 HIGH" if impact == 'high' else "🟡 MEDIUM" if impact == 'medium' else "⚪ LOW"
                    weight = 3 if impact == 'high' else 2 if impact == 'medium' else 1
                    
                    results.append({
                        "Time": item['date'].split('T')[1][:5], # แสดงเวลา HH:MM
                        "Currency": item['currency'],
                        "Headline": item['title'],
                        "Volatility": v_score,
                        "Sentiment": label['label'],
                        "Confidence": f"{label['score']:.2%}",
                        "Weight": weight,
                        "Source": "Forex Factory"
                    })
    except Exception:
        # หาก Forex Factory ล่ม จะไม่แสดง Error สีแดง แต่จะพยายามดึงข้อมูลจากแหล่งอื่นแทน
        pass

    # ดึงข้อมูลสำรองจาก Investing.com RSS หากปฏิทินหลักมีปัญหา
    try:
        feed = feedparser.parse("https://www.investing.com/rss/news_285.rss")
        for entry in feed.entries[:5]:
            label = analyzer(entry.title)[0]
            results.append({
                "Time": "LIVE",
                "Currency": "ALL",
                "Headline": entry.title,
                "Volatility": "🟡 MEDIUM",
                "Sentiment": label['label'],
                "Confidence": f"{label['score']:.2%}",
                "Weight": 1,
                "Source": "Investing.com"
            })
    except:
        pass
    
    return results

# --- 4. การแสดงผลหน้าจอ Dashboard ---
st.title("🏦 Gold AI Expert Specialist")
st.markdown(f"**Live Analysis: ประจำวันที่** {datetime.now().strftime('%d %B 2026')}")

# ปุ่มสำหรับ Refresh ข้อมูล
if st.button('🔄 Sync & Expert Re-analyze'):
    st.cache_data.clear()

with st.spinner('AI กำลังตรวจสอบข่าวสดและวิเคราะห์ทิศทางทองคำ...'):
    news_data = get_live_expert_news()

if news_data:
    df = pd.DataFrame(news_data)
    
    # --- ส่วนสรุปกลยุทธ์ทองคำ ---
    st.header("✨ Today's Gold Strategy")
    
    # คำนวณความแข็งแกร่ง (อิงตาม Sentiment และ Weight)
    bull_power = sum(df[df['Sentiment'] == 'POSITIVE']['Weight'])
    bear_power = sum(df[df['Sentiment'] == 'NEGATIVE']['Weight'])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Bullish Power 💪", bull_power)
    c2.metric("Bearish Power 📉", bear_power)
    
    with c3:
        if bull_power > bear_power:
            st.success("### AI BIAS: 🚀 BUY GOLD")
        elif bear_power > bull_power:
            st.error("### AI BIAS: 📉 SELL GOLD")
        else:
            st.warning("### AI BIAS: ⚖️ NEUTRAL")

    st.divider()
    
    # --- ตารางรายละเอียดข่าวพร้อมเวลาและระดับความแรง ---
    st.subheader("📑 Live News Feed & Volatility Analysis")
    st.dataframe(df[['Time', 'Source', 'Headline', 'Volatility', 'Sentiment', 'Confidence']], use_container_width=True)
    
    # แจ้งเตือนหากมีข่าวแรง (High Impact)
    high_impact_list = df[df['Volatility'].str.contains("🔴")]
    if not high_impact_list.empty:
        st.warning(f"🚨 **ระวัง:** พบข่าวระดับ High Impact {len(high_impact_list)} รายการในวันนี้!")
else:
    # แสดงคำแนะนำหากเชื่อมต่อแหล่งข่าวหลักไม่ได้
    st.error("⚠️ **Connection Error:** ไม่สามารถดึงข้อมูลสดได้ชั่วคราว (Network Timeout)")
    st.info("คำแนะนำ: ตรวจสอบการเชื่อมต่ออินเทอร์เน็ตของระบบ หรือกดปุ่ม Sync อีกครั้งในภายหลัง")
    st.write("ขณะนี้ยังไม่มีข่าวเศรษฐกิจสำคัญประกาศ หรือระบบกำลังรอการตอบกลับจากแหล่งข่าวใหม่")
