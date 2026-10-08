# -*- coding: utf-8 -*-
"""
AI Model Tracker Engine.
Monitors RSS feeds, GitHub Releases, Anthropic news scraper, and Hugging Face Hub APIs.
Applies a strict 48-hour freshness filter so old models (6 months / 1 year) are NEVER posted.
"""

import time
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from bs4 import BeautifulSoup
import html

from config import (
    BOT_TOKEN,
    CHANNEL_CHAT_ID,
    MAX_AGE_HOURS,
    AI_RSS_FEEDS,
    GITHUB_RELEASE_FEEDS,
    HF_TRACKED_ORGS
)
from database import is_item_seen, mark_item_seen, log_broadcast

DEFAULT_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"'
}

def is_recent_date(date_str: str, max_hours: int = MAX_AGE_HOURS) -> bool:
    """
    Check if a publication date / ISO timestamp is within the last `max_hours`.
    Filters out models and articles that are months or years old.
    """
    if not date_str:
        return False
    try:
        dt = date_parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - dt
        # Must be within past max_hours and not far in the future
        return timedelta(seconds=0) <= diff <= timedelta(hours=max_hours)
    except Exception:
        # If date parsing fails, be conservative
        return False

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

def send_telegram_message(text: str, parse_mode: str = "HTML", max_retries: int = 3) -> tuple[bool, str]:
    """
    Send formatted notification to the target Telegram Channel.
    - Disables web page link previews completely.
    - Automatically handles Telegram rate limits (HTTP 429) with exponential backoff.
    """
    if not BOT_TOKEN or not CHANNEL_CHAT_ID:
        return False, "Bot Token or Channel ID is missing in configuration."

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
        "link_preview_options": {
            "is_disabled": True
        }
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=20)
            res_data = response.json()
            
            if response.status_code == 200 and res_data.get("ok"):
                return True, "Broadcast posted successfully."
            
            # Handle HTTP 429: Too Many Requests
            if response.status_code == 429:
                retry_after = res_data.get("parameters", {}).get("retry_after", 5)
                time.sleep(retry_after + 1)
                continue
            
            err_desc = res_data.get("description", "Unknown Telegram API error")
            return False, f"Telegram API Error ({response.status_code}): {err_desc}"
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return False, "Telegram API Timeout: Request timed out."
        except Exception as e:
            return False, f"Network / Request Exception: {str(e)}"

    return False, "Telegram API Error (429): Rate limited after retries."

def format_rss_post(entry, source: dict) -> str:
    """Format an RSS / Atom feed update into an attractive Telegram HTML post."""
    title = html.escape(entry.get("title", "New AI Update"))
    link = entry.get("link", "")
    summary = clean_html(entry.get("summary", entry.get("description", "")))
    
    published = entry.get("published", entry.get("updated", datetime.now(timezone.utc).strftime("%Y-%m-%d")))
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
    created_at = model.get("createdAt", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
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

def fetch_anthropic_news() -> list:
    """
    Directly scrapes Anthropic's news announcements from https://www.anthropic.com/news
    because Anthropic does not provide an official public RSS feed.
    """
    announcements = []
    url = "https://www.anthropic.com/news"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            seen_links = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/news/") and len(href) > 6:
                    full_link = f"https://www.anthropic.com{href}"
                    if full_link in seen_links:
                        continue
                    seen_links.add(full_link)
                    
                    text_parts = [p.strip() for p in a.get_text(separator="\n").split("\n") if p.strip()]
                    title = ""
                    summary = ""
                    date_text = ""
                    for p in text_parts:
                        if any(m in p for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                            date_text = p
                        elif len(p) > len(title):
                            summary = title
                            title = p
                    
                    if title:
                        announcements.append({
                            "title": title,
                            "link": full_link,
                            "summary": summary,
                            "published": date_text or datetime.now(timezone.utc).strftime("%b %d, %Y"),
                            "company": "Anthropic",
                            "region": "🇺🇸 USA",
                            "category": "Claude & Frontier AI"
                        })
    except Exception as e:
        print(f"Error scraping Anthropic: {e}")
    return announcements

def run_tracking_cycle(broadcast_to_telegram: bool = True) -> dict:
    """
    Execute one complete tracking pass with strict 48-hour lookback:
    1. Anthropic Live News Scraper
    2. Curated RSS/Atom Feeds (Google DeepMind, OpenAI, Meta, Google Developers, etc.)
    3. GitHub Release Atom Feeds
    4. Hugging Face Model APIs
    """
    new_found = 0
    new_broadcasted = 0
    errors = []

    # --- 1. Anthropic Live News Scraper ---
    anthropic_items = fetch_anthropic_news()
    for item in anthropic_items:
        item_id = item["link"]
        if is_item_seen(item_id):
            continue
            
        pub_date = item.get("published", "")
        # Apply freshness check (last 48 hours)
        if not is_recent_date(pub_date, MAX_AGE_HOURS):
            # Mark seen so we don't re-parse old news
            mark_item_seen(item_id, "Anthropic News", "Anthropic", item["title"], item["link"], pub_date)
            continue
            
        new_found += 1
        if broadcast_to_telegram:
            formatted_msg = format_rss_post(item, item)
            success, resp_msg = send_telegram_message(formatted_msg)
            if success:
                new_broadcasted += 1
                mark_item_seen(item_id, "Anthropic News", "Anthropic", item["title"], item["link"], pub_date)
                log_broadcast(item_id, item["title"], "Anthropic", "SUCCESS", resp_msg)
                time.sleep(2.5)
            else:
                errors.append(f"Anthropic: {resp_msg}")
                log_broadcast(item_id, item["title"], "Anthropic", "FAILED", resp_msg)
        else:
            mark_item_seen(item_id, "Anthropic News", "Anthropic", item["title"], item["link"], pub_date)

    # --- 2. Process RSS / Atom Feeds ---
    all_feeds = AI_RSS_FEEDS + GITHUB_RELEASE_FEEDS
    for feed_info in all_feeds:
        try:
            # Fetch with browser headers to avoid Cloudflare/403 blocks
            try:
                resp = requests.get(feed_info["url"], headers=DEFAULT_BROWSER_HEADERS, timeout=12)
                feed = feedparser.parse(resp.content) if resp.status_code == 200 else feedparser.parse(feed_info["url"])
            except Exception:
                feed = feedparser.parse(feed_info["url"])
                
            if not feed.entries:
                continue
                
            for entry in feed.entries[:5]:
                item_id = entry.get("id") or entry.get("link") or entry.get("title")
                if not item_id:
                    continue
                
                if is_item_seen(item_id):
                    continue
                    
                pub_date = entry.get("published", entry.get("updated", ""))
                title = entry.get("title", "AI Update")
                link = entry.get("link", "")
                
                # Check strict freshness: only last 48 hours
                if not is_recent_date(pub_date, MAX_AGE_HOURS):
                    # Silently mark seen so old articles are skipped permanently
                    mark_item_seen(item_id, feed_info["name"], feed_info["company"], title, link, pub_date)
                    continue
                    
                new_found += 1
                if broadcast_to_telegram:
                    formatted_msg = format_rss_post(entry, feed_info)
                    success, resp_msg = send_telegram_message(formatted_msg)
                    
                    if success:
                        new_broadcasted += 1
                        mark_item_seen(item_id, feed_info["name"], feed_info["company"], title, link, pub_date)
                        log_broadcast(item_id, title, feed_info["company"], "SUCCESS", resp_msg)
                        time.sleep(2.5)
                    else:
                        errors.append(f"{feed_info['name']}: {resp_msg}")
                        log_broadcast(item_id, title, feed_info["company"], "FAILED", resp_msg)
                else:
                    mark_item_seen(item_id, feed_info["name"], feed_info["company"], title, link, pub_date)
                    
        except Exception as e:
            errors.append(f"Feed error ({feed_info.get('name')}): {str(e)}")

    # --- 3. Process Hugging Face Hub Model APIs ---
    for org_info in HF_TRACKED_ORGS:
        org = org_info["org"]
        api_url = f"https://huggingface.co/api/models?author={org}&sort=createdAt&direction=-1&limit=5"
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
                        
                    created_at = model.get("createdAt", "")
                    
                    # Check strict freshness: only last 48 hours
                    if not is_recent_date(created_at, MAX_AGE_HOURS):
                        # Silently mark seen so old models from months ago are never posted
                        mark_item_seen(item_key, "Hugging Face Hub", org_info["company"], model_id, f"https://huggingface.co/{model_id}", created_at)
                        continue
                        
                    new_found += 1
                    if broadcast_to_telegram:
                        formatted_msg = format_hf_post(model, org_info)
                        success, resp_msg = send_telegram_message(formatted_msg)
                        
                        if success:
                            new_broadcasted += 1
                            mark_item_seen(item_key, "Hugging Face Hub", org_info["company"], model_id, f"https://huggingface.co/{model_id}", created_at)
                            log_broadcast(item_key, model_id, org_info["company"], "SUCCESS", resp_msg)
                            time.sleep(2.5)
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
