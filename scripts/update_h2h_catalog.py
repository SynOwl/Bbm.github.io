#!/usr/bin/env python3
"""Refresh the current month's official Hearts2Hearts MV catalog from YouTube RSS.

The current month replaces the previous month by design. Instagram is linked as an
official source, but its posts are not scraped: Meta access is not reliably available
without an authorized API token/account.
"""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

CHANNEL_ID = "UC7Q3HUnJA3nvjZR2JeMn2Cw"
INSTAGRAM_PROFILE = "https://www.instagram.com/hearts2hearts/"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
OUT = Path("data/h2h-monthly.json")
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

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
            published = parsedate_to_datetime(published_raw) if "," in published_raw else datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        if published.astimezone(timezone.utc).strftime("%Y-%m") != month:
            continue
        videos.append({
            "id": video_id,
            "title": title,
            "published": published.astimezone(timezone.utc).isoformat(),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "source": "youtube-official",
        })

    videos.sort(key=lambda item: item["published"], reverse=True)
    payload = {
        "schemaVersion": 1,
        "month": month,
        "updatedAt": now.isoformat(),
        "source": {
            "youtube": "https://www.youtube.com/@hearts2hearts.official",
            "instagram": INSTAGRAM_PROFILE,
        },
        "instagramAutomation": {
            "status": "manual-link-required",
            "note": "Automatic Instagram Reel ingestion requires authorized access; no unreliable scraping is used.",
        },
        "videos": videos,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(videos)} official MV(s) for {month} to {OUT}")

if __name__ == "__main__":
    main()
