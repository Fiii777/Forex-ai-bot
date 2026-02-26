import streamlit as st
import feedparser
import pandas as pd
import asyncio
from transformers import pipeline
from telegram import Bot
import time

# --- การตั้งค่าเบื้องต้น ---
st.set_page_config(page_title="Forex AI 24/7 Hub", layout="wide")

# ใส่ข้อมูลของคุณที่นี่ (หรือใช้ Streamlit Secrets เพื่อความปลอดภัย)
TELEGRAM_TOKEN = '8789659037:AAFE23eEJplsKVE8tx1_qCVIfZYfWcY-vuE'
CHAT_ID = '6323430163'

# โหลด AI (Caching ไว้เพื่อไม่ให้โหลดใหม่ทุกรอบที่รีเฟรชหน้าเว็บ)
@st.cache_resource
def load_ai():
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

nlp = load_ai()
telegram_bot = Bot(token=TELEGRAM_TOKEN)

# --- ฟังก์ชันการทำงาน ---
def fetch_and_analyze():
    rss_url = "https://www.forexfactory.com/news/rss"
    feed = feedparser.parse(rss_url)
    results = []
    
    for entry in feed.entries[:15]:
        sentiment = nlp(entry.title)[0]
        results.append({
            "Time": entry.published,
            "Headline": entry.title,
            "Label": sentiment['label'],
            "Score": sentiment['score'],
            "Link": entry.link
        })
    return results

async def send_telegram_alert(news_item):
    label = news_item['Label']
    score = news_item['Score']
    emoji = "🟢 Bullish" if label == "positive" else "🔴 Bearish"
    
    if score > 0.85 and label != "neutral":
        msg = (
            f"⚠️ *Forex AI Alert*\n"
            f"━━━━━━━━━━━━\n"
            f"📰 {news_item['Headline']}\n\n"
            f"🎯 *Analysis:* {emoji}\n"
            f"📊 *Confidence:* {score:.2%}\n"
            f"━━━━━━━━━━━━\n"
            f"🔗 [Read More]({news_item['Link']})"
        )
        try:
            await telegram_bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
        except Exception as e:
            st.error(f"Telegram Error: {e}")

# --- ส่วนหน้าจอ Web Dashboard ---
st.title("🤖 Forex AI Intelligence Hub (24/7)")
st.write("ระบบวิเคราะห์ข่าวอัตโนมัติและแจ้งเตือนผ่าน Telegram")

if st.button('🔄 Refresh Data Now'):
    st.cache_data.clear()

# ดึงข้อมูลมาแสดงผล
news_data = fetch_and_analyze()

if not news_data:
    st.warning("⚠️ ยังไม่มีข้อมูลข่าวในขณะนี้ กำลังรอการอัปเดต...")
else:
    df = pd.DataFrame(news_data)
    
    # ตรวจสอบว่ามีคอลัมน์ Label จริงๆ ก่อนเริ่มคำนวณ
    if 'Label' in df.columns:
        # ส่วน Metric ด้านบน (โค้ดเดิมของคุณ)
        c1, c2, c3 = st.columns(3)
        pos = len(df[df['Label'] == 'positive'])
        neg = len(df[df['Label'] == 'negative'])
        c1.metric("Positive News", pos)
        c2.metric("Negative News", neg)
        c3.metric("Overall Bias", "BUY" if pos > neg else "SELL" if neg > pos else "NEUTRAL")

        # แสดงตารางวิเคราะห์
        st.subheader("Latest Analysis")
        st.dataframe(df[['Time', 'Headline', 'Label', 'Score']], use_container_width=True)
    else:
        st.error("❌ AI กำลังประมวลผลข้อมูล กรุณากด Refresh อีกครั้งในอีก 10 วินาที")

# --- ระบบทำงานอัตโนมัติ (Background Loop) ---
# ในการรันบน Streamlit Cloud เราจะใช้กลไกเช็คข่าวล่าสุด
if 'last_headline' not in st.session_state:
    st.session_state.last_headline = ""

# เช็คก่อนว่ามีข่าวอยู่ใน list จริงๆ ไหม
if len(news_data) > 0:
    latest_news = news_data[0]
    if latest_news['Headline'] != st.session_state.last_headline:
        st.session_state.last_headline = latest_news['Headline']
        asyncio.run(send_telegram_alert(latest_news))
        st.toast(f"🔔 ส่งแจ้งเตือนข่าวใหม่แล้ว: {latest_news['Headline'][:30]}...")
else:
    st.info("ℹ️ กำลังรอสัญญาณข่าวใหม่จาก Server...")

st.info("💡 เว็บนี้จะอัปเดตตัวเองและส่งข่าวใหม่เข้า Telegram ทุกครั้งที่มีคนเปิดหน้าเว็บ หรือคุณสามารถตั้งค่า Cron Job ให้มา Trigger เว็บได้")
# --- ส่วนหน้าจอ Web Dashboard ---
st.title("🤖 Forex AI Intelligence Hub (24/7)")
st.write("ระบบวิเคราะห์ข่าวอัตโนมัติและแจ้งเตือนผ่าน Telegram")


# ดึงข้อมูลมาประมวลผล
news_data = fetch_and_analyze()

if not news_data:
    st.warning("⚠️ ยังไม่มีข้อมูลข่าวในขณะนี้ กำลังรอการอัปเดต...")
else:
    # สร้าง DataFrame เฉพาะเมื่อมีข้อมูล
    df = pd.DataFrame(news_data)
    
    # ตรวจสอบว่า AI ประมวลผลคอลัมน์ Label เสร็จเรียบร้อย
    if 'Label' in df.columns:
        # 1. ส่วน Metric ด้านบน
        c1, c2, c3 = st.columns(3)
        pos_count = len(df[df['Label'] == 'positive'])
        neg_count = len(df[df['Label'] == 'negative'])
        
        c1.metric("Positive News", pos_count)
        c2.metric("Negative News", neg_count)
        
        bias = "NEUTRAL ⚖️"
        if pos_count > neg_count: bias = "BUY 📈"
        elif neg_count > pos_count: bias = "SELL 📉"
        c3.metric("Overall Bias", bias)

        # 2. แสดงตารางวิเคราะห์
        st.subheader("Latest Analysis")
        st.dataframe(df[['Time', 'Headline', 'Label', 'Score']], use_container_width=True)

        # 3. ระบบทำงานอัตโนมัติ (Telegram Alert)
        if 'last_headline' not in st.session_state:
            st.session_state.last_headline = ""

        latest_news = news_data[0]
        if latest_news['Headline'] != st.session_state.last_headline:
            st.session_state.last_headline = latest_news['Headline']
            asyncio.run(send_telegram_alert(latest_news))
            st.toast(f"🔔 ส่งแจ้งเตือนข่าวใหม่แล้ว: {latest_news['Headline'][:30]}...")
    else:

        st.error("❌ โครงสร้างข้อมูลไม่ถูกต้อง กรุณารีเฟรชหน้าเว็บอีกครั้ง")
