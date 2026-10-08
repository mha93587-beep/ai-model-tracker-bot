# -*- coding: utf-8 -*-
"""
Streamlit Web Dashboard & Background Polling Engine for Telegram AI Model Tracker.
Optimized for Streamlit Community Cloud free hosting.
"""

import streamlit as st
import time
import threading
import pandas as pd
from datetime import datetime

from config import (
    BOT_TOKEN,
    CHANNEL_CHAT_ID,
    CHANNEL_USERNAME,
    CHECK_INTERVAL_SECONDS,
    AI_RSS_FEEDS,
    GITHUB_RELEASE_FEEDS,
    HF_TRACKED_ORGS
)
from database import (
    get_stats,
    get_recent_broadcasts,
    init_db
)
from tracker import (
    run_tracking_cycle,
    send_telegram_message
)

# Page configuration
st.set_page_config(
    page_title="AI Model Tracker Bot - Control Panel",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure database tables are created
init_db()

# --- Background Worker Singleton Pattern (Streamlit Cloud Optimized) ---
class BackgroundWorker:
    def __init__(self):
        self.is_running = True
        self.interval = CHECK_INTERVAL_SECONDS
        self.last_run = None
        self.last_status = "Waiting for first cycle"
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        # Initial cold start wait
        time.sleep(5)
        while True:
            if self.is_running:
                try:
                    self.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    result = run_tracking_cycle(broadcast_to_telegram=True)
                    self.last_status = f"Completed at {self.last_run} (Found: {result['new_found']}, Sent: {result['new_broadcasted']})"
                except Exception as e:
                    self.last_status = f"Error in cycle: {str(e)}"
            
            # Sleep in 5-second intervals to allow fast pause/resume
            for _ in range(max(1, self.interval // 5)):
                if not self.is_running:
                    break
                time.sleep(5)

@st.cache_resource
def get_background_worker():
    """Starts the background tracking daemon exactly once across all Streamlit sessions."""
    return BackgroundWorker()

worker = get_background_worker()

# --- Custom UI CSS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 13px;
    }
    .badge-active {
        background-color: #1f6feb;
        color: #ffffff;
    }
    .badge-success {
        background-color: #238636;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.title("🤖 Model Tracker Bot")
st.sidebar.markdown(f"**Channel:** [{CHANNEL_USERNAME}]({CHANNEL_USERNAME})")
st.sidebar.markdown(f"**Chat ID:** `{CHANNEL_CHAT_ID}`")

masked_token = f"{BOT_TOKEN[:10]}...{BOT_TOKEN[-6:]}" if BOT_TOKEN else "❌ Not Configured"
st.sidebar.markdown(f"**Bot Token:** `{masked_token}`")

st.sidebar.divider()
st.sidebar.subheader("⚙️ Worker Settings")

worker.interval = st.sidebar.slider(
    "Check Interval (Seconds)",
    min_value=60,
    max_value=1800,
    value=worker.interval,
    step=60,
    help="Default is 300 seconds (5 minutes)."
)

col_w1, col_w2 = st.sidebar.columns(2)
if col_w1.button("⏸️ Pause", use_container_width=True):
    worker.is_running = False
    st.sidebar.warning("Worker paused.")

if col_w2.button("▶️ Resume", use_container_width=True):
    worker.is_running = True
    st.sidebar.success("Worker resumed.")

st.sidebar.divider()
st.sidebar.info("""
**Cloud Hosting Note:**
Hosted on **Streamlit Community Cloud**.
To keep the worker running 24/7 without sleep, add your app URL to a free uptime monitor (e.g., UptimeRobot).
""")

# --- Main Dashboard Header ---
st.title("🚀 Global AI Model Tracker - Telegram Broadcaster")
st.caption("24/7 Real-Time Indexer for New AI Models, Version Releases & Research Updates.")

# --- Action & Status Bar ---
col_act1, col_act2, col_act3 = st.columns([2, 1, 1])

with col_act1:
    status_color = "#238636" if worker.is_running else "#da3633"
    status_text = "🟢 Background Worker Active" if worker.is_running else "🔴 Background Worker Paused"
    st.markdown(f"### <span style='color:{status_color}'>{status_text}</span>", unsafe_allow_html=True)
    st.caption(f"Last Status: `{worker.last_status}` | Last Run: `{worker.last_run or 'Just Started'}`")

with col_act2:
    if st.button("⚡ Check & Broadcast Now", type="primary", use_container_width=True):
        with st.spinner("Scanning all RSS feeds, GitHub releases & Hugging Face APIs..."):
            res = run_tracking_cycle(broadcast_to_telegram=True)
            if res["new_broadcasted"] > 0:
                st.success(f"Success! Found {res['new_found']} new items and broadcasted {res['new_broadcasted']} posts!")
            elif res["new_found"] > 0:
                st.info(f"Found {res['new_found']} new items (Check logs if Telegram broadcast failed).")
            else:
                st.info("Everything is up to date! No new releases found in this pass.")
            if res["errors"]:
                st.error("Some feed warnings: " + "; ".join(res["errors"][:3]))

with col_act3:
    if st.button("🔔 Send Test Post", use_container_width=True):
        test_msg = (
            "🤖 <b>AI MODEL TRACKER TEST BROADCAST</b>\n\n"
            "✅ <i>Streamlit Cloud worker connection is working successfully!</i>\n"
            f"🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            "📡 <i>Channel: @modeltracker</i>"
        )
        success, msg = send_telegram_message(test_msg)
        if success:
            st.success("Test broadcast successfully sent to Telegram channel!")
        else:
            st.error(f"Failed to send test message: {msg}")

st.divider()

# --- Metrics Overview ---
stats = get_stats()
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

total_feeds = len(AI_RSS_FEEDS) + len(GITHUB_RELEASE_FEEDS)
total_orgs = len(HF_TRACKED_ORGS)

col_m1.metric("RSS / Atom Feeds", f"{total_feeds} Sources")
col_m2.metric("Tracked AI Orgs (HF)", f"{total_orgs} Orgs")
col_m3.metric("Total Models/Updates Indexed", f"{stats['total_indexed']} Items")
col_m4.metric("Broadcasts Sent to Telegram", f"{stats['total_broadcasts']} Posts")

st.divider()

# --- Tabs ---
tab_logs, tab_sources, tab_manual, tab_config = st.tabs([
    "📜 Broadcast Logs & History",
    "🏢 Tracked AI Companies & Feeds",
    "➕ Test & Manual Broadcast",
    "⚙️ Streamlit Cloud Deployment Guide"
])

with tab_logs:
    st.subheader("Recent Broadcasts to @modeltracker")
    logs = get_recent_broadcasts(limit=50)
    if logs:
        df_logs = pd.DataFrame(logs)
        # Reorder and rename
        display_df = df_logs[["sent_at", "company", "title", "status", "message"]].rename(
            columns={
                "sent_at": "Time",
                "company": "Company / Lab",
                "title": "Title / Model ID",
                "status": "Status",
                "message": "API Result"
            }
        )
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No broadcasts sent yet. Click 'Check & Broadcast Now' or wait for the automatic cycle.")

with tab_sources:
    st.subheader("Active Sources & Monitored Feeds")
    
    st.markdown("#### 1. Curated AI Blogs & RSS Feeds")
    df_rss = pd.DataFrame(AI_RSS_FEEDS + GITHUB_RELEASE_FEEDS)[["name", "company", "region", "category", "url"]]
    st.dataframe(df_rss, use_container_width=True)
    
    st.markdown("#### 2. Hugging Face Lab Hub Monitors (Direct Model Weight Uploads)")
    df_hf = pd.DataFrame(HF_TRACKED_ORGS)[["company", "country", "org"]]
    st.dataframe(df_hf, use_container_width=True)

with tab_manual:
    st.subheader("Send Custom Announcement / Alert to Channel")
    with st.form("custom_broadcast_form"):
        cust_title = st.text_input("Model / Update Title", placeholder="e.g. DeepSeek-V4 Announced!")
        cust_company = st.text_input("Company / Organization", placeholder="e.g. DeepSeek / OpenAI / Sarvam AI")
        cust_link = st.text_input("Link / URL", placeholder="https://...")
        cust_summary = st.text_area("Summary / Description", placeholder="Brief description of the model features...")
        submit_btn = st.form_submit_button("🚀 Broadcast to @modeltracker")
        
        if submit_btn:
            if not cust_title or not cust_company:
                st.warning("Please provide at least Title and Company name.")
            else:
                custom_post = (
                    f"🚨 <b>AI UPDATE ANNOUNCEMENT</b>\n\n"
                    f"🏢 <b>Company:</b> {cust_company}\n"
                    f"📌 <b>Title:</b> {cust_title}\n\n"
                )
                if cust_summary:
                    custom_post += f"📝 <b>Summary:</b>\n<i>{cust_summary}</i>\n\n"
                if cust_link:
                    custom_post += f"🔗 <b>Link:</b> {cust_link}\n\n"
                custom_post += "📡 <i>Channel: @modeltracker</i>"
                
                success, msg = send_telegram_message(custom_post)
                if success:
                    st.success("Custom announcement sent to Telegram channel!")
                else:
                    st.error(f"Failed to send: {msg}")

with tab_config:
    st.subheader("☁️ Streamlit Community Cloud Deployment Guide")
    st.markdown("""
### Steps to Deploy for 24/7 Free Hosting:

1. **GitHub Repository Banayein:**
   - Apne GitHub account par ek naya repository create karein (e.g. `ai-model-tracker-bot`).
   - Is folder (`/storage/emulated/0/antigravity/RamuaRSS/`) ki sabhi files ko us repository me push karein:
     - `app.py`
     - `tracker.py`
     - `config.py`
     - `database.py`
     - `requirements.txt`
     - `.streamlit/config.toml`

2. **Streamlit Cloud par Connect Karein:**
   - [share.streamlit.io](https://share.streamlit.io) par login karein.
   - **"New app"** par click karein aur apna GitHub repo select karein.
   - Main file path me `app.py` set karein.

3. **Secrets Add Karein (Crucial for Security):**
   - **"Advanced settings"** -> **"Secrets"** section me jayein.
   - Niche diye gaye credentials paste karein:
   ```toml
   BOT_TOKEN = "8807868607:AAGZzOYFfft5HJ2SDOEfnczpFc_wbBxWih8"
   CHANNEL_CHAT_ID = "-1004454876267"
   CHANNEL_USERNAME = "https://t.me/modeltracker"
   CHECK_INTERVAL_SECONDS = 300
   ```
   - **"Deploy"** button dabayein!

4. **24/7 Active / Keep-Alive Rakhna:**
   - Streamlit Cloud free apps kuch din bina visitor ke sleep mode me ja sakte hain.
   - Ise 24/7 awake rakhne ke liye free service jaise [UptimeRobot.com](https://uptimerobot.com) ya [cron-job.org](https://cron-job.org) me apne Streamlit app ka URL daal kar har 10-15 minute ka HTTP ping laga dein.
   - Isse bot cloud me bina ruke 24 ghante automatic nayi AI model releases Telegram channel par post karta rahega!
    """)
