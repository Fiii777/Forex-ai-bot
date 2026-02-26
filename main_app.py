import streamlit as st
import feedparser
import requests
import pandas as pd
import asyncio
from transformers import pipeline
from telegram import Bot

# --- 1. ตั้งค่าหน้าจอ (UI Setup) ---
st.set_page_config(page_title="Forex AI Intel Hub", layout="wide", page_icon="🤖")

# --- 2. โหลด AI Sentiment (FinBERT) ---
@st.cache_resource
def load_ai():
    # FinBERT คือโมเดลที่ถูกฝึกมาเพื่ออ่านข่าวการเงินโดยเฉพาะ
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

sentiment_pipeline = load_ai()

# --- 3. ดึงความลับจาก Secrets (Telegram) ---
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

async def send_telegram_alert(news_item):
    if TELEGRAM_TOKEN and CHAT_ID:
        try:
            bot = Bot(token=TELEGRAM_TOKEN)
            msg = (f"🔔 AI FOREX ALERT!\n\n"
                   f"📰 {news_item['Headline']}\n"
                   f"🏛 Source: {news_item['Source']}\n"
                   f"🤖 Sentiment: {news_item['Label'].upper()}\n"
                   f"📊 Score: {news_item['Score']}")
            await bot.send_message(chat_id=CHAT_ID, text=msg)
        except: pass

# --- 4. ฟังก์ชันดึงข่าว (Multi-Source & Forex Factory) ---
def fetch_global_news():
    all_news = []
    
    # ดึงจาก RSS (Investing, Yahoo, DailyFX)
    rss_urls = {
        "Investing.com": "https://www.investing.com/rss/news_285.rss",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "DailyFX": "https://www.dailyfx.com/feeds/forex-market-news"
    }
    
    for name, url in rss_urls.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                res = sentiment_pipeline(entry.title)[0]
                all_news.append({
                    "Source": name,
                    "Time": entry.get('published', 'N/A'),
                    "Headline": entry.title,
                    "Label": res['label'],
                    "Score": round(res['score'], 2)
                })
        except: continue

    # ดึงจาก Forex Factory (Calendar)
    try:
        ff_url = "https://cdn-nfs.forexfactory.net/ff_calendar_thisweek.json"
        response = requests.get(ff_url, headers={'User-Agent': 'Mozilla/5.0'})
        for item in response.json()[:7]:
            headline = f"[{item['currency']}] {item['title']} (Impact: {item['impact']})"
            res = sentiment_pipeline(item['title'])[0]
            all_news.append({
                "Source": "Forex Factory",
                "Time": item['date'],
                "Headline": headline,
                "Label": res['label'],
                "Score": round(res['score'], 2)
            })
    except: pass
    
    return all_news

# --- 5. หน้าจอ Dashboard ---
st.title("🤖 Forex AI Intelligence Hub (24/7)")
st.write("ระบบวิเคราะห์ข่าวเศรษฐกิจโลกอัตโนมัติด้วย AI")

if st.button('🔄 Refresh & Sync Data'):
    st.cache_data.clear()

with st.spinner('AI กำลังประมวลผลทิศทางตลาด...'):
    news_data = fetch_global_news()

if news_data:
    df = pd.DataFrame(news_data)
    
    # ส่วนคำนวณ Bias (Buy/Sell)
    c1, c2, c3 = st.columns(3)
    pos = len(df[df['Label'] == 'positive'])
    neg = len(df[df['Label'] == 'negative'])
    
    c1.metric("Bullish News 📈", pos)
    c2.metric("Bearish News 📉", neg)
    
    with c3:
        if pos > neg: st.success("Overall: BUY BIAS 🚀")
        elif neg > pos: st.error("Overall: SELL BIAS 📉")
        else: st.info("Overall: NEUTRAL ⚖️")

    st.divider()
    
    # แสดงตารางสวยงาม
    st.subheader("📊 ตารางวิเคราะห์ข่าว Real-time")
    st.dataframe(df, use_container_width=True)

    # ระบบ Telegram (ส่งข่าวล่าสุด)
    if 'last_headline' not in st.session_state:
        st.session_state.last_headline = ""
    
    latest_news = news_data[0]
    if latest_news['Headline'] != st.session_state.last_headline:
        st.session_state.last_headline = latest_news['Headline']
        asyncio.run(send_telegram_alert(latest_news))
        st.toast(f"🔔 แจ้งเตือนส่งเข้า Telegram แล้ว!")
else:
    st.warning("⚠️ กำลังดึงข้อมูลจาก Server... กรุณารอสักครู่")
