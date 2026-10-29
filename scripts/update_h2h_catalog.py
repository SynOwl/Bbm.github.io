#!/usr/bin/env python3
"""Refresh current-month official Hearts2Hearts MV entries from the official YouTube RSS."""
from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

CHANNEL_ID = "UC7Q3HUnJA3nvjZR2JeMn2Cw"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
OUT = Path("data/h2h-monthly.json")
NS = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}

def main():
    now = datetime.now(timezone.utc)
    month = now.strftime("%Y-%m")
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": "BBM-H2H-Monthly-Updater/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        root = ET.fromstring(response.read())
    videos = []
    for entry in root.findall("atom:entry", NS):
        title = (entry.findtext("atom:title", default="", namespaces=NS) or "").strip()
        video_id = (entry.findtext("yt:videoId", default="", namespaces=NS) or "").strip()
        published_raw = (entry.findtext("atom:published", default="", namespaces=NS) or "").strip()
        if not video_id or not title or "mv" not in title.lower():
            continue
        try:
            published = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        if published.astimezone(timezone.utc).strftime("%Y-%m") != month:
            continue
        videos.append({
            "id": video_id, "title": title,
            "published": published.astimezone(timezone.utc).isoformat(),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "source": "youtube-official"
        })
    videos.sort(key=lambda v: v["published"], reverse=True)
    payload = {
        "schemaVersion": 1, "month": month, "updatedAt": now.isoformat(),
        "source": {"youtube": "https://www.youtube.com/@hearts2hearts.official",
                   "instagram": "https://www.instagram.com/hearts2hearts/"},
        "instagramAutomation": {
            "status": "manual-link-required",
            "note": "Automatic Instagram Reel ingestion requires authorized API access; no unreliable scraping is used."
        },
        "videos": videos
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(videos)} official MV(s) for {month}")

if __name__ == "__main__":
    main()
