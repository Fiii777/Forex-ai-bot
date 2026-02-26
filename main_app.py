import streamlit as st
import requests
import pandas as pd
from transformers import pipeline
from datetime import datetime, date

# --- 1. การตั้งค่าหน้าจอและ Theme (Professional UI) ---
st.set_page_config(page_title="Gold AI Expert Specialist", layout="wide", page_icon="🏦")

# --- 2. โหลด AI Sentiment (DistilBERT) ---
@st.cache_resource
def load_sentiment_ai():
    # ใช้โมเดลที่เสถียรและแม่นยำสำหรับการรันบน Streamlit Cloud
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

analyzer = load_sentiment_ai()

# --- 3. ฟังก์ชันดึงข่าวล่าสุดของวันนี้ (2026) ---
def get_live_expert_news():
    results = []
    today_str = date.today().strftime('%Y-%m-%d')
    
    try:
        # ดึงข้อมูลจาก Forex Factory (Economic Calendar)
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        ff_res = requests.get(ff_url, timeout=10)
        if ff_res.status_code == 200:
            for item in ff_res.json():
                # กรองเฉพาะข่าวที่ประกาศในวันนี้ของปี 2026 เท่านั้น
                if today_str in item['date']:
                    label = analyzer(item['title'])[0]
                    
                    # กำหนดระดับความแรงของข่าว (Volatility)
                    impact = item['impact'].lower()
                    v_score = "🔴 HIGH" if impact == 'high' else "🟡 MEDIUM" if impact == 'medium' else "⚪ LOW"
                    weight = 3 if impact == 'high' else 2 if impact == 'medium' else 1
                    
                    results.append({
                        "Time": item['date'].split('T')[1][:5], # แสดงเฉพาะเวลา HH:MM
                        "Currency": item['currency'],
                        "Headline": item['title'],
                        "Volatility": v_score,
                        "Sentiment": label['label'],
                        "Confidence": f"{label['score']:.2%}",
                        "Weight": weight
                    })
    except Exception as e:
        st.error(f"⚠️ Connection Error: ไม่สามารถดึงข้อมูลสดได้ ({e})")
    
    return results

# --- 4. การวิเคราะห์ความสัมพันธ์และกลยุทธ์ทองคำ ---
def show_gold_strategy(df):
    st.header("✨ XAU/USD Gold Strategy Dashboard")
    
    # วิเคราะห์ทิศทางดอลลาร์ (USD) ที่ส่งผลต่อทองคำ
    usd_news = df[df['Currency'] == 'USD']
    usd_pos = len(usd_news[usd_news['Sentiment'] == 'POSITIVE'])
    usd_neg = len(usd_news[usd_news['Sentiment'] == 'NEGATIVE'])
    
    # คำนวณพลังของฝั่ง Bullish และ Bearish สำหรับทองคำ
    # (ทองคำมักวิ่งสวนทางกับข่าว USD)
    gold_bull_power = sum(df[df['Sentiment'] == 'POSITIVE']['Weight']) - usd_pos + usd_neg
    gold_bear_power = sum(df[df['Sentiment'] == 'NEGATIVE']['Weight']) - usd_neg + usd_pos

    c1, c2, c3 = st.columns(3)
    c1.metric("Gold Bullish Power 💪", max(0, gold_bull_power))
    c2.metric("Gold Bearish Power 📉", max(0, gold_bear_power))
    
    with c3:
        if gold_bull_power > gold_bear_power:
            st.success("### AI BIAS: 🚀 BUY GOLD")
        elif gold_bear_power > gold_bull_power:
            st.error("### AI BIAS: 📉 SELL GOLD")
        else:
            st.warning("### AI BIAS: ⚖️ NEUTRAL")

    # ส่วนแจ้งเตือนความรุนแรง (Volatility Alert)
    high_impact = df[df['Volatility'].str.contains("🔴")]
    if not high_impact.empty:
        st.warning(f"🚨 **Volatility Alert:** มีข่าวแรง {len(high_impact)} ข่าวในวันนี้ ระวังการสวิงของราคาทองคำ!")

# --- 5. การแสดงผลหน้าจอหลัก ---
st.title("🏦 Gold AI Expert Specialist")
st.markdown(f"**Live Analysis:** ประจำวันที่ {datetime.now().strftime('%d %B 2026')}")

# ปุ่ม Sync ข้อมูล
if st.button('🔄 Sync & Expert Re-analyze'):
    st.cache_data.clear()

# ประมวลผลและแสดงผล
with st.spinner('AI กำลังวิเคราะห์ข้อมูลตลาดสด...'):
    news_data = get_live_expert_news()

if news_data:
    df_final = pd.DataFrame(news_data)
    
    # แสดง Dashboard กลยุทธ์
    show_gold_strategy(df_final)
    
    st.divider()
    
    # แสดงตารางรายละเอียดข่าว
    st.subheader("📑 Live News & Volatility Feed")
    # จัดเรียงตามเวลาล่าสุด
    st.dataframe(df_final[['Time', 'Currency', 'Headline', 'Volatility', 'Sentiment', 'Confidence']], use_container_width=True)
else:
    st.info("☕ ขณะนี้ยังไม่มีข่าวเศรษฐกิจสำคัญประกาศในวันนี้ หรือระบบกำลังรอการเชื่อมต่อใหม่")
    st.write("คำแนะนำ: ตรวจสอบตารางข่าวพรุ่งนี้ หรือกด Refresh อีกครั้ง")
