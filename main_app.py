import streamlit as st
import requests
import pandas as pd
from transformers import pipeline
from datetime import datetime, date

# --- 1. ตั้งค่าหน้าจอ (Pro Theme) ---
st.set_page_config(page_title="Gold AI Expert Pro", layout="wide", page_icon="🏦")

# --- 2. โหลด AI แบบประหยัดพลังงาน ---
@st.cache_resource
def load_sentiment_ai():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

analyzer = load_sentiment_ai()

# --- 3. ฟังก์ชันดึงข่าวล่าสุดพร้อมวิเคราะห์ Volatility ---
def get_expert_news():
    results = []
    today_str = date.today().strftime('%Y-%m-%d')
    
    try:
        # ดึงจาก Forex Factory (Calendar)
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        ff_res = requests.get(ff_url, timeout=7)
        if ff_res.status_code == 200:
            for item in ff_res.json():
                if today_str in item['date']:
                    analysis = analyzer(item['title'])[0]
                    # ระบบคำนวณ Volatility Score
                    impact = item['impact'].lower()
                    v_score = "🔥 HIGH" if impact == 'high' else "⚡ MEDIUM" if impact == 'medium' else "💨 LOW"
                    
                    results.append({
                        "Time": item['date'].split('T')[1][:5],
                        "Currency": item['currency'],
                        "Headline": item['title'],
                        "Volatility": v_score,
                        "Sentiment": analysis['label'],
                        "Confidence": analysis['score'],
                        "Impact_Raw": impact
                    })
    except:
        pass
    return results

# --- 4. ระบบวิเคราะห์ความสัมพันธ์ (Correlation & Confirmation) ---
def gold_correlation_analysis(news_df):
    st.subheader("🏦 Gold Correlation & Market Pulse")
    
    # กรองข่าว USD เพื่อดูทิศทางดอลลาร์
    usd_news = news_df[news_df['Currency'] == 'USD']
    usd_positive = len(usd_news[usd_news['Sentiment'] == 'POSITIVE'])
    usd_negative = len(usd_news[usd_news['Sentiment'] == 'NEGATIVE'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        if usd_negative > usd_positive:
            st.success(f"✅ **USD Weakness Identified:** พบข่าวลบต่อดอลลาร์ {usd_negative} ข่าว (หนุนราคาทองคำ)")
        elif usd_positive > usd_negative:
            st.error(f"⚠️ **USD Strength Alert:** พบข่าวบวกต่อดอลลาร์ {usd_positive} ข่าว (กดดันราคาทองคำ)")
        else:
            st.info("⚖️ **USD Neutral:** ทิศทางดอลลาร์ยังไม่ชัดเจน")
            
    with col2:
        high_vol = len(news_df[news_df['Impact_Raw'] == 'high'])
        if high_vol > 0:
            st.warning(f"🚨 **Volatility Alert:** มีข่าว High Impact {high_vol} ข่าว! กราฟอาจสวิงแรงเกิน 1,000 จุด")
        else:
            st.info("🟢 **Market Calm:** สภาพคล่องปกติ ไม่พบข่าวรุนแรงพิเศษ")

# --- 5. Dashboard หลัก ---
st.title("🏦 Gold AI Expert Specialist")
st.markdown(f"**Live Analysis:** วางแผนเทรดทองคำประจำวันที่ {datetime.now().strftime('%d %B 2026')}")

if st.button('🔄 Sync & Expert Re-analyze'):
    st.cache_data.clear()

with st.spinner('AI กำลังตรวจสอบความสัมพันธ์ของตลาดและทิศทางทองคำ...'):
    data = get_expert_news()

if data:
    df = pd.DataFrame(data)
    
    # ส่วนวิเคราะห์ Correlation
    gold_correlation_analysis(df)
    
    st.divider()
    
    # สรุป Bias รายวัน
    st.header("✨ Daily Trading Strategy")
    
    # คำนวณคะแนนทองคำ (สวนทาง USD)
    gold
