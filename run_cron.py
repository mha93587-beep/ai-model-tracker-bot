# -*- coding: utf-8 -*-
"""
Standalone CLI entry point for running the tracking cycle.
Used by GitHub Actions and system crons.
"""

import sys
import os

from tracker import run_tracking_cycle
from database import get_stats

if __name__ == "__main__":
    print("🚀 Running AI Model Tracker Cycle...")
    res = run_tracking_cycle(broadcast_to_telegram=True)
    stats = get_stats()
    print(f"✅ Finished cycle: Found {res['new_found']} items, Broadcasted {res['new_broadcasted']} posts.")
    print(f"📊 Stats: {stats}")
    if res["errors"]:
        print("⚠️ Warnings:", res["errors"][:3])
