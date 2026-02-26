import streamlit as st
import feedparser
import requests
import pandas as pd
import asyncio
from transformers import pipeline

# --- 1. ตั้งค่าพื้นฐาน (ป้องกันหน้าจอซ้ำ) ---
st.set_page_config(page_title="Pro Forex AI Hub", layout="wide")

# --- 2. โหลด AI แบบประหยัดพลังงาน ---
@st.cache_resource
def load_sentiment_ai(): # <--- ตรวจสอบว่าชื่อฟังก์ชันคือ load_sentiment_ai
    # ใช้โมเดลพื้นฐานที่เบาและโหลดไว
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# บรรทัดที่ 17: เรียกใช้ชื่อให้ตรงกับด้านบน
analyzer = load_sentiment_ai()

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

# --- ส่วนคำแนะนำจาก AI ---
st.subheader("💡 AI Trade Strategy")
if gold_pos > gold_neg:
    st.success("กลยุทธ์: **ย่อซื้อ (Buy on Dip)** - ข่าวส่วนใหญ่ส่งผลบวกต่อทองคำ")
elif gold_neg > gold_pos:
    st.error("กลยุทธ์: **เด้งขาย (Sell on Rally)** - ข่าวส่วนใหญ่กดดันราคาทองคำ")
else:
    st.warning("กลยุทธ์: **รอดูสถานการณ์ (Wait & See)** - สัญญาณข่าวยังไม่ชัดเจน")
    
# --- ฟังก์ชันวิเคราะห์เจาะจงทองคำ (XAU/USD) ---
def get_gold_analysis():
    gold_data = []
    
    # 1. ดึงข่าวที่มีคีย์เวิร์ดเกี่ยวกับ Gold, XAU, Fed, Inflation, USD
    keywords = ['gold', 'xau', 'fed', 'inflation', 'usd', 'fomc', 'interest rate']
    
    # ดึงจากแหล่งข่าวหลัก
    raw_news = get_forex_news() # ใช้ฟังก์ชันเดิมที่คุณมี
    
    for news in raw_news:
        headline_lower = news['Headline'].lower()
        # กรองเฉพาะข่าวที่เกี่ยวข้องกับทองคำ
        if any(key in headline_lower for key in keywords):
            # เพิ่ม Logic วิเคราะห์ผลกระทบต่อทองคำ
            if news['AI Sentiment'] == 'POSITIVE' and ('usd' not in headline_lower):
                gold_impact = "🚀 BULLISH FOR GOLD"
            elif news['AI Sentiment'] == 'NEGATIVE' and ('usd' in headline_lower):
                gold_impact = "🚀 BULLISH FOR GOLD (USD Weakness)"
            elif news['AI Sentiment'] == 'POSITIVE' and ('usd' in headline_lower):
                gold_impact = "📉 BEARISH FOR GOLD (USD Strength)"
            else:
                gold_impact = "⚖️ NEUTRAL / VOLATILE"
                
            news['Gold Impact'] = gold_impact
            gold_data.append(news)
            
    return gold_data

# --- ส่วนการแสดงผลใหม่บน Dashboard ---
st.header("✨ XAU/USD Gold Special Analysis")
gold_news = get_gold_analysis()

if gold_news:
    gold_df = pd.DataFrame(gold_news)
    # แสดงเข็มไมล์หรือ Metric สำหรับทองคำโดยเฉพาะ
    gold_pos = len(gold_df[gold_df['Gold Impact'].str.contains("BULLISH")])
    gold_neg = len(gold_df[gold_df['Gold Impact'].str.contains("BEARISH")])
    
    col1, col2 = st.columns(2)
    col1.metric("Gold Bullish Signals", gold_pos)
    col2.metric("Gold Bearish Signals", gold_neg)
    
    st.subheader("📊 Gold Focused News Table")
    st.dataframe(gold_df[['Source', 'Headline', 'AI Sentiment', 'Gold Impact']], use_container_width=True)
else:
    st.write("คัดกรองแล้ว ยังไม่มีข่าวที่มีผลกระทบต่อทองคำโดยตรงในขณะนี้")
    
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

