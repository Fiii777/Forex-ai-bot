import streamlit as st
import feedparser
import requests
import pandas as pd
import asyncio
from transformers import pipeline
from telegram import Bot

# --- 1. ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Pro Forex AI Dashboard", layout="wide")

# --- 2. โหลด AI Sentiment (FinBERT) ---
@st.cache_resource
def load_ai():
    # โมเดลนี้ถูกฝึกมาเพื่ออ่านข่าวการเงินโดยเฉพาะ แม่นยำกว่าโมเดลทั่วไป
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

sentiment_pipeline = load_ai()

# --- 3. ตั้งค่า Telegram (ดึงจาก Secrets) ---
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

async def send_telegram_alert(news_item):
    if TELEGRAM_TOKEN and CHAT_ID:
        try:
            bot = Bot(token=TELEGRAM_TOKEN)
            msg = (f"🔔 AI ANALYSIS ALERT!\n\n"
                   f"📰 Headline: {news_item['Headline']}\n"
                   f"🏛 Source: {news_item['Source']}\n"
                   f"🤖 AI Sentiment: {news_item['Label'].upper()}\n"
                   f"📊 Confidence: {news_item['Score']}")
            await bot.send_message(chat_id=CHAT_ID, text=msg)
        except Exception as e:
            print(f"Telegram Error: {e}")

# --- 4. ฟังก์ชันดึงข่าวจากแหล่งต่างๆ ---
def fetch_all_sources():
    all_data = []
    
    # --- ส่วนที่ 1: ดึงจาก RSS (Investing, Yahoo, DailyFX) ---
    rss_sources = {
        "Investing.com": "https://www.investing.com/rss/news_285.rss",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "DailyFX": "https://www.dailyfx.com/feeds/forex-market-news"
    }
    
    for name, url in rss_sources.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                res = sentiment_pipeline(entry.title)[0]
                all_data.append({
                    "Source": name,
                    "Time": entry.get('published', 'N/A'),
                    "Headline": entry.title,
                    "Label": res['label'],
                    "Score": round(res['score'], 2)
                })
        except: continue

    # --- ส่วนที่ 2: ดึงจาก Forex Factory (Calendar JSON) ---
    try:
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        response = requests.get(ff_url, headers={'User-Agent': 'Mozilla/5.0'})
        ff_data = response.json()
        for item in ff_data[:10]: # ดึง 10 ข่าวเศรษฐกิจล่าสุด
            # วิเคราะห์ Sentiment จากหัวข้อข่าวเศรษฐกิจ
            headline = f"[{item['currency']}] {item['title']} (Impact: {item['impact']})"
            res = sentiment_pipeline(item['title'])[0]
            all_data.append({
                "Source": "Forex Factory",
                "Time": item['date'],
                "Headline": headline,
                "Label": res['label'],
                "Score": round(res['score'], 2)
            })
    except: pass
    
    return all_data

# --- 5. ส่วนแสดงผล Dashboard ---
st.title("🤖 Pro Forex AI Intelligence Hub")
st.markdown("ระบบวิเคราะห์ Sentiment ข่าวทั่วโลกจาก **Forex Factory, Investing, Yahoo**")

if st.button('🔄 Sync & Analyze Latest News'):
    st.cache_data.clear()

with st.spinner('AI กำลังอ่านข่าวและวิเคราะห์ทิศทางตลาด...'):
    news_list = fetch_all_sources()

if news_list:
    df = pd.DataFrame(news_list)
    
    # --- ส่วนวิเคราะห์ BUY/SELL BIAS ---
    c1, c2, c3 = st.columns(3)
    pos = len(df[df['Label'] == 'positive'])
    neg = len(df[df['Label'] == 'negative'])
    
    with c1:
        st.metric("Bullish News 📈", pos, delta="Positive Sentiment")
    with c2:
        st.metric("Bearish News 📉", neg, delta="-Negative Sentiment", delta_color="inverse")
    with c3:
        if pos > neg:
            st.success("### Overall Bias: STRONG BUY 🚀")
        elif neg > pos:
            st.error("### Overall Bias: STRONG SELL 📉")
        else:
            st.warning("### Overall Bias: NEUTRAL ⚖️")

    st.divider()

    # --- แสดงตารางข้อมูล ---
    st.subheader("📊 ตารางวิเคราะห์ข่าวแบบ Real-time")
    # ตกแต่งสีในตาราง
    def color_label(val):
        color = '#2ecc71' if val == 'positive' else '#e74c3c' if val == 'negative' else '#95a5a6'
        return f'background-color: {color}; color: white; font-weight: bold'
    
    st.dataframe(df.style.applymap(color_label, subset=['Label']), use_container_width=True)

    # --- 6. ระบบส่ง Telegram อัตโนมัติ ---
    if 'last_headline' not in st.session_state:
        st.session_state.last_headline = ""

    if df.iloc[0]['Headline'] != st.session_state.last_headline:
        st.session_state.last_headline = df.iloc[0]['Headline']
        asyncio.run(send_telegram_alert(news_list[0]))
        st.toast(f"🔔 ส่งแจ้งเตือนข่าวล่าสุดแล้ว!")

else:
    st.warning("ไม่สามารถดึงข้อมูลได้ในขณะนี้ กรุณากดปุ่ม Refresh อีกครั้ง")