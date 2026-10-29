#!/usr/bin/env python3
"""Refresh all current-month uploads from the official Hearts2Hearts YouTube channel RSS."""
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
        if not video_id or not title or not published_raw:
            continue
        try:
            published = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        published = published.astimezone(timezone.utc)
        if published.strftime("%Y-%m") != month:
            continue
        is_mv = "mv" in title.lower()
        videos.append({
            "id": video_id, "title": title, "type": "mv" if is_mv else "youtube",
            "published": published.isoformat(),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "source": "youtube-official"
        })
    # RSS has a limited recent-upload window, so retain this month's already collected entries.
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding="utf-8"))
            if previous.get("month") == month:
                known = {v.get("id"): v for v in previous.get("videos", []) if v.get("id")}
                known.update({v["id"]: v for v in videos})
                videos = list(known.values())
        except (OSError, ValueError, TypeError):
            pass
    videos.sort(key=lambda v: v["published"], reverse=True)
    payload = {
        "schemaVersion": 2, "month": month, "updatedAt": now.isoformat(),
        "source": {"youtube": "https://www.youtube.com/@hearts2hearts.official"},
        "collectionPolicy": "All official YouTube uploads from the current month; previous month's collection is replaced.",
        "videos": videos
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(videos)} official YouTube upload(s) for {month}")

if __name__ == "__main__":
    main()
