import streamlit as st
import feedparser
import requests
import pandas as pd
from transformers import pipeline

# --- 1. ตั้งค่าหน้าจอ (Professional UI) ---
st.set_page_config(page_title="Gold AI Pro Hub", layout="wide", page_icon="🟡")

# --- 2. โหลด AI แบบประหยัดพลังงาน ---
@st.cache_resource
def load_sentiment_ai():
    # ใช้ DistilBERT เพื่อความไวและเสถียรบน Streamlit Cloud
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

analyzer = load_sentiment_ai()

# --- 3. ฟังก์ชันดึงข่าวและวิเคราะห์น้ำหนัก (Impact & Confidence) ---
def get_advanced_news():
    results = []
    # ดึงข้อมูลจาก Forex Factory
    try:
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        ff_res = requests.get(ff_url, timeout=10)
        for item in ff_res.json()[:15]: 
            analysis = analyzer(item['title'])[0]
            # ระบบถ่วงน้ำหนักตามระดับความรุนแรงของข่าว
            weight = 3 if item['impact'].lower() == 'high' else 2 if item['impact'].lower() == 'medium' else 1
            impact_icon = "🔴" if item['impact'].lower() == 'high' else "🟡" if item['impact'].lower() == 'medium' else "⚪"
            
            results.append({
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

    # ดึงจาก Investing.com
    try:
        feed = feedparser.parse("https://www.investing.com/rss/news_285.rss")
        for entry in feed.entries[:5]:
            analysis = analyzer(entry.title)[0]
            results.append({
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

# --- 4. ตรรกะวิเคราะห์เจาะจงทองคำ (XAU/USD Gold Analysis) ---
def analyze_gold_impact(news_list):
    gold_report = []
    keywords = ['gold', 'xau', 'fed', 'inflation', 'usd', 'cpi', 'interest rate', 'fomc']
    
    for news in news_list:
        h_lower = news['Headline'].lower()
        if any(k in h_lower for k in keywords) or news['Currency'] == 'USD':
            # ความสัมพันธ์แบบสวนทาง: USD แข็ง = ทองลง | USD อ่อน = ทองขึ้น
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

# --- 5. หน้า Dashboard ---
st.title("🟡 Gold AI Pro Specialist Hub")
st.markdown("ระบบวิเคราะห์ Sentiment เจาะลึก **ทองคำ (XAU/USD)** และข่าวเศรษฐกิจโลกด้วย AI")

# ปุ่ม Refresh
if st.button('🔄 Sync Data & Re-analyze Market'):
    st.cache_data.clear()

with st.spinner('AI กำลังวิเคราะห์ผลกระทบต่อตลาด...'):
    news_data = get_advanced_news()
    gold_news = analyze_gold_impact(news_data)

if news_data:
    df = pd.DataFrame(news_data)
    
    # --- ส่วนที่ 1: วิเคราะห์ทองคำ (XAU/USD) ---
    st.header("✨ Gold Trading Strategy")
    g_col1, g_col2, g_col3 = st.columns(3)
    
    gold_pos = sum(n['Weight'] for n in gold_news if "BULLISH" in n['Gold_Action'])
    gold_neg = sum(n['Weight'] for n in gold_news if "BEARISH" in n['Gold_Action'])
    
    g_col1.metric("Gold Bullish Power 💪", gold_pos)
    g_col2.metric("Gold Bearish Power 📉", gold_neg)
    
    with g_col3:
        st.subheader("💡 AI Strategy")
        if gold_pos > gold_neg:
            st.success("กลยุทธ์: **BUY ON DIP (ย่อซื้อ)**")
        elif gold_neg > gold_pos:
            st.error("กลยุทธ์: **SELL ON RALLY (เด้งขาย)**")
        else:
            st.warning("กลยุทธ์: **WAIT & SEE (รอดูสถานการณ์)**")

    # ตารางวิเคราะห์ทองคำโดยเฉพาะ
    with st.expander("🔍 รายละเอียดการวิเคราะห์เจาะจงทองคำ", expanded=True):
        if gold_news:
            st.dataframe(pd.DataFrame(gold_news)[['Headline', 'Impact', 'Gold_Action']], use_container_width=True)
        else:
            st.write("ยังไม่มีข่าวที่ส่งผลกระทบต่อทองคำโดยตรง")

    st.divider()

    # --- ส่วนที่ 2: สรุปภาพรวมตลาด Forex ---
    st.header("🌎 Global Market Overview")
    c1, c2, c3 = st.columns(3)
    pos_count = len(df[df['AI Sentiment'] == 'POSITIVE'])
    neg_count = len(df[df['AI Sentiment'] == 'NEGATIVE'])
    
    c1.metric("Bullish News", pos_count)
    c2.metric("Bearish News", neg_count)
    
    overall_bias = "STRONG BUY" if pos_count > neg_count else "STRONG SELL" if neg_count > pos_count else "NEUTRAL"
    c3.subheader(f"Overall Bias: {overall_bias}")

    # ตารางข่าวทั้งหมด
    st.subheader("📑 รายละเอียดการวิเคราะห์ข่าวทั้งหมด")
    st.dataframe(df[['Source', 'Currency', 'Headline', 'Impact', 'AI Sentiment', 'Confidence']], use_container_width=True)

    # --- ส่วนที่ 3: Top High Confidence (ของแถม) ---
    st.divider()
    st.subheader("🔥 Top 3 High Confidence Analysis")
    top_news = df.sort_values(by="Raw_Score", ascending=False).head(3)
    for _, row in top_news.iterrows():
        st.info(f"🎯 **{row['Headline']}** | Sentiment: {row['AI Sentiment']} ({row['Confidence']})")

else:
    st.warning("⚠️ ไม่พบข้อมูลข่าวในขณะนี้ กรุณากดปุ่ม Refresh อีกครั้ง")
