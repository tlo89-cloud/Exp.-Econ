#!/usr/bin/env python3
"""
inject_events.py — ONLY writes events.json, never touches the HTML.
The HTML fetches events.json dynamically at runtime via JavaScript fetch().
"""

import json
from pathlib import Path
from datetime import datetime, timezone

EVENTS_FILE = Path(__file__).parent / "events.json"

def run():
    print("✅ inject_events.py: events.json is updated by scraper.py directly.")
    print("   The HTML fetches events.json dynamically — no HTML injection needed.")
    if EVENTS_FILE.exists():
        with open(EVENTS_FILE) as f:
            events = json.load(f)
        print(f"   Total events in events.json: {len(events)}")
        high_quality = [e for e in events if e.get('score', 0) >= 7]
        print(f"   High-quality (score≥7, shown on timeline): {len(high_quality)}")
    else:
        print("   events.json not found — will be created on next scraper run.")

if __name__ == "__main__":
    run()
