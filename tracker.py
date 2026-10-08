# -*- coding: utf-8 -*-
"""
AI Model Tracker Engine.
Monitors RSS feeds, GitHub Releases, and Hugging Face model hub APIs,
formats updates, and broadcasts new releases to Telegram channel.
"""

import time
import requests
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup
import html

from config import (
    BOT_TOKEN,
    CHANNEL_CHAT_ID,
    AI_RSS_FEEDS,
    GITHUB_RELEASE_FEEDS,
    HF_TRACKED_ORGS
)
from database import is_item_seen, mark_item_seen, log_broadcast

def clean_html(raw_html: str, max_chars: int = 300) -> str:
    """Strip HTML tags and truncate text for clean Telegram preview."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    text = html.escape(text)
    if len(text) > max_chars:
        return text[:max_chars].rsplit(" ", 1)[0] + "..."
    return text

def send_telegram_message(text: str, parse_mode: str = "HTML") -> tuple[bool, str]:
    """
    Send formatted notification to the target Telegram Channel.
    Returns (success: bool, status_message: str).
    """
    if not BOT_TOKEN or not CHANNEL_CHAT_ID:
        return False, "Bot Token or Channel ID is missing in configuration."

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        res_data = response.json()
        
        if response.status_code == 200 and res_data.get("ok"):
            return True, "Broadcast posted successfully."
        else:
            err_desc = res_data.get("description", "Unknown Telegram API error")
            return False, f"Telegram API Error ({response.status_code}): {err_desc}"
    except requests.exceptions.Timeout:
        return False, "Telegram API Timeout: Request timed out."
    except Exception as e:
        return False, f"Network / Request Exception: {str(e)}"

def format_rss_post(entry, source: dict) -> str:
    """Format an RSS / Atom feed update into an attractive Telegram HTML post."""
    title = html.escape(entry.get("title", "New AI Update"))
    link = entry.get("link", "")
    summary = clean_html(entry.get("summary", entry.get("description", "")))
    
    published = entry.get("published", entry.get("updated", datetime.utcnow().strftime("%Y-%m-%d")))
    company = source.get("company", "AI Lab")
    region = source.get("region", "Global")
    category = source.get("category", "AI Updates")
    
    hashtag_comp = company.replace(" ", "").replace("-", "").replace("/", "")
    hashtag_cat = category.replace(" ", "").replace("&", "").replace("-", "")

    msg = (
        f"🚨 <b>NEW AI RELEASE / ANNOUNCEMENT</b>\n\n"
        f"🏢 <b>Company / Lab:</b> {company} ({region})\n"
        f"📌 <b>Title:</b> {title}\n"
        f"🏷 <b>Category:</b> #{hashtag_comp} #{hashtag_cat} #AIModel\n\n"
    )
    if summary:
        msg += f"📝 <b>Summary:</b>\n<i>{summary}</i>\n\n"
        
    msg += (
        f"🔗 <b>Full Details / Link:</b>\n{link}\n\n"
        f"🕒 <b>Published:</b> {published}\n"
        f"📡 <i>Channel: @modeltracker</i>"
    )
    return msg

def format_hf_post(model: dict, org_info: dict) -> str:
    """Format a Hugging Face new model launch into a Telegram HTML post."""
    model_id = model.get("id", "")
    created_at = model.get("createdAt", datetime.utcnow().strftime("%Y-%m-%d"))
    pipeline = model.get("pipeline_tag", "Foundation / Multimodal")
    company = org_info.get("company", "AI Lab")
    country = org_info.get("country", "Global")
    
    model_url = f"https://huggingface.co/{model_id}"
    comp_tag = company.replace(" ", "").replace("-", "").replace("/", "")
    
    msg = (
        f"🔥 <b>NEW AI MODEL LAUNCHED ON HUB</b>\n\n"
        f"🏢 <b>Organization:</b> {company} ({country})\n"
        f"📦 <b>Model ID:</b> <code>{html.escape(model_id)}</code>\n"
        f"⚙️ <b>Pipeline / Modality:</b> {pipeline}\n"
        f"🏷 <b>Tags:</b> #NewModel #{comp_tag} #OpenWeights\n\n"
        f"📥 <b>Weights & Model Card:</b>\n{model_url}\n\n"
        f"🕒 <b>Released At:</b> {created_at}\n"
        f"📡 <i>Channel: @modeltracker</i>"
    )
    return msg

def run_tracking_cycle(broadcast_to_telegram: bool = True) -> dict:
    """
    Execute one complete tracking pass across:
    1. Curated RSS/Atom Feeds
    2. GitHub Release Atom Feeds
    3. Hugging Face Model APIs
    """
    new_found = 0
    new_broadcasted = 0
    errors = []

    # --- 1. Process RSS / Atom Feeds ---
    all_feeds = AI_RSS_FEEDS + GITHUB_RELEASE_FEEDS
    for feed_info in all_feeds:
        try:
            feed = feedparser.parse(feed_info["url"])
            if not feed.entries:
                continue
                
            # Process the latest 3 entries from each feed
            for entry in feed.entries[:3]:
                item_id = entry.get("id") or entry.get("link") or entry.get("title")
                if not item_id:
                    continue
                
                # Check duplicate
                if is_item_seen(item_id):
                    continue
                    
                new_found += 1
                title = entry.get("title", "AI Update")
                link = entry.get("link", "")
                pub_date = entry.get("published", entry.get("updated", ""))

                if broadcast_to_telegram:
                    formatted_msg = format_rss_post(entry, feed_info)
                    success, resp_msg = send_telegram_message(formatted_msg)
                    
                    if success:
                        new_broadcasted += 1
                        mark_item_seen(item_id, feed_info["name"], feed_info["company"], title, link, pub_date)
                        log_broadcast(item_id, title, feed_info["company"], "SUCCESS", resp_msg)
                        time.sleep(1.5)  # Telegram API gentle delay
                    else:
                        errors.append(f"{feed_info['name']}: {resp_msg}")
                        log_broadcast(item_id, title, feed_info["company"], "FAILED", resp_msg)
                else:
                    # Mark seen without broadcasting (e.g. cold start)
                    mark_item_seen(item_id, feed_info["name"], feed_info["company"], title, link, pub_date)
                    
        except Exception as e:
            errors.append(f"Feed error ({feed_info.get('name')}): {str(e)}")

    # --- 2. Process Hugging Face Hub Model APIs ---
    for org_info in HF_TRACKED_ORGS:
        org = org_info["org"]
        api_url = f"https://huggingface.co/api/models?author={org}&sort=createdAt&direction=-1&limit=2"
        try:
            r = requests.get(api_url, timeout=10)
            if r.status_code == 200:
                models = r.json()
                for model in models:
                    model_id = model.get("id")
                    if not model_id:
                        continue
                        
                    item_key = f"hf_model_{model_id}"
                    if is_item_seen(item_key):
                        continue
                        
                    new_found += 1
                    created_at = model.get("createdAt", "")
                    
                    if broadcast_to_telegram:
                        formatted_msg = format_hf_post(model, org_info)
                        success, resp_msg = send_telegram_message(formatted_msg)
                        
                        if success:
                            new_broadcasted += 1
                            mark_item_seen(item_key, "Hugging Face Hub", org_info["company"], model_id, f"https://huggingface.co/{model_id}", created_at)
                            log_broadcast(item_key, model_id, org_info["company"], "SUCCESS", resp_msg)
                            time.sleep(1.5)
                        else:
                            errors.append(f"HF {org}: {resp_msg}")
                            log_broadcast(item_key, model_id, org_info["company"], "FAILED", resp_msg)
                    else:
                        mark_item_seen(item_key, "Hugging Face Hub", org_info["company"], model_id, f"https://huggingface.co/{model_id}", created_at)
                        
        except Exception as e:
            errors.append(f"HF Org error ({org}): {str(e)}")

    return {
        "new_found": new_found,
        "new_broadcasted": new_broadcasted,
        "errors": errors
    }
