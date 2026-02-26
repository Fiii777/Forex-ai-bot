import streamlit as st
import feedparser
from transformers import pipeline
import pandas as pd
import asyncio
from telegram import Bot

# --- ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Forex Multi-Source AI", layout="wide")

# --- โหลด AI (ใช้ Cache เพื่อความเร็ว) ---
@st.cache_resource
def load_ai():
    # ใช้โมเดลที่เก่งด้านการเงินโดยเฉพาะ
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

sentiment_pipeline = load_ai()

# --- ตั้งค่า Telegram (ใส่เลขของคุณตรงนี้) ---
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", "YOUR_TOKEN_HERE")
CHAT_ID = st.secrets.get("CHAT_ID", "YOUR_ID_HERE")

async def send_telegram_alert(news):
    if TELEGRAM_TOKEN != "YOUR_TOKEN_HERE":
        bot = Bot(token=TELEGRAM_TOKEN)
        msg = f"🔔 ข่าวใหม่วิเคราะห์แล้ว!\n📌 {news['Headline']}\n🤖 AI บอกว่า: {news['Label'].upper()}\n📊 Score: {news['Score']}"
        await bot.send_message(chat_id=CHAT_ID, text=msg)

# --- ฟังก์ชันดึงข่าวจากหลายแหล่ง ---
def fetch_multi_news():
    sources = {
        "Investing.com": "https://www.investing.com/rss/news_285.rss",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "DailyFX": "https://www.dailyfx.com/feeds/forex-market-news"
    }
    
    all_news = []
    for name, url in sources.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # ดึงที่ละ 5 ข่าวล่าสุดต่อแหล่ง
                res = sentiment_pipeline(entry.title)[0]
                all_news.append({
                    "Source": name,
                    "Time": entry.get('published', 'N/A'),
                    "Headline": entry.title,
                    "Label": res['label'],
                    "Score": round(res['score'], 2)
                })
        except:
            continue
    return all_news

# --- ส่วนการแสดงผลบนเว็บ ---
st.title("🌎 Forex Global Intelligence AI")
st.write("วิเคราะห์ข่าวรวมจากหลายแหล่งระดับโลก เพื่อหา Bias ทิศทางตลาด")

if st.button('🔄 Refresh Global News'):
    st.cache_data.clear()

data = fetch_multi_news()

if data:
    df = pd.DataFrame(data)
    
    # --- ส่วนวิเคราะห์ BUY/SELL Bias ---
    c1, c2, c3 = st.columns(3)
    
    # นับจำนวน Positive / Negative (FinBERT จะให้ผลเป็น positive, negative, neutral)
    pos = len(df[df['Label'] == 'positive'])
    neg = len(df[df['Label'] == 'negative'])
    
    with c1:
        st.metric("Bullish News (Positive)", pos, delta=f"{pos} ข่าว", delta_color="normal")
    with c2:
        st.metric("Bearish News (Negative)", neg, delta=f"-{neg} ข่าว", delta_color="inverse")
    with c3:
        # คำนวณหาทิศทางหลัก
        if pos > neg:
            bias, color = "📈 BUY BIAS", "green"
        elif neg > pos:
            bias, color = "📉 SELL BIAS", "red"
        else:
            bias, color = "⚖️ NEUTRAL", "gray"
        st.subheader(f"Overall: :{color}[{bias}]")

    # --- แสดงตารางข่าวแยกตามแหล่ง ---
    st.divider()
    st.subheader("📊 รายละเอียดวิเคราะห์รายข่าว")
    st.dataframe(df, use_container_width=True)
    
    # --- ระบบ Telegram (ส่งเฉพาะข่าวล่าสุด 1 ข่าว) ---
    if 'last_news' not in st.session_state:
        st.session_state.last_news = ""
    
    if df.iloc[0]['Headline'] != st.session_state.last_news:
        st.session_state.last_news = df.iloc[0]['Headline']
        asyncio.run(send_telegram_alert(data[0]))
        st.toast("✅ แจ้งเตือนส่งเข้า Telegram แล้ว")
else:
    st.info("กำลังรอข้อมูลข่าว...")