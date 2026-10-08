# -*- coding: utf-8 -*-
"""
Database manager for tracking indexed AI model releases and broadcast logs.
Uses SQLite for zero-configuration, reliable persistence.
"""

import sqlite3
import os
from datetime import datetime
from config import DB_PATH

def get_connection():
    """Create a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table 1: Track all processed items / articles / models
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indexed_items (
            item_id TEXT PRIMARY KEY,
            source_name TEXT,
            company TEXT,
            title TEXT,
            url TEXT,
            published_at TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table 2: Broadcast logs sent to Telegram channel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS broadcast_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT,
            title TEXT,
            company TEXT,
            status TEXT,
            message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def is_item_seen(item_id: str) -> bool:
    """Check if an item ID has already been indexed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM indexed_items WHERE item_id = ?", (item_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def mark_item_seen(item_id: str, source_name: str, company: str, title: str, url: str, published_at: str):
    """Save an item ID to prevent duplicate broadcasting."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO indexed_items (item_id, source_name, company, title, url, published_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (item_id, source_name, company, title, url, published_at))
        conn.commit()
    finally:
        conn.close()

def log_broadcast(item_id: str, title: str, company: str, status: str, message: str = ""):
    """Log an attempted or successful Telegram broadcast."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO broadcast_logs (item_id, title, company, status, message)
            VALUES (?, ?, ?, ?, ?)
        """, (item_id, title, company, status, message))
        conn.commit()
    finally:
        conn.close()

def get_recent_broadcasts(limit: int = 50):
    """Retrieve the latest broadcasts for dashboard display."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, item_id, title, company, status, message, sent_at
        FROM broadcast_logs
        ORDER BY sent_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_stats():
    """Retrieve total count statistics for dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM indexed_items")
    total_indexed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM broadcast_logs WHERE status = 'SUCCESS'")
    total_broadcasts = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_indexed": total_indexed,
        "total_broadcasts": total_broadcasts
    }

# Ensure DB is created on load
init_db()
