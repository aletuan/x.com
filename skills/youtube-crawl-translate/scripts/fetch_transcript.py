#!/usr/bin/env python3
"""
Fetch YouTube transcript (EN only) via Apify.
Chỉ Apify — không fallback web fetch. Chỉ tiếng Anh để có kết quả nhanh nhất.
Usage: python fetch_transcript.py <video_id>
Output: JSON to stdout [{text, start, duration}, ...]
"""
import json
import os
import sys
from pathlib import Path

# Load .env from project root (parent of skills/)
project_root = Path(__file__).resolve().parents[3]
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)


def _normalize_segments(transcript: list) -> list:
    """Normalize to [{text, start, duration}, ...]."""
    if not transcript:
        return []
    s0 = transcript[0]
    if "startMs" in (s0 or {}):
        return [
            {
                "text": s["text"],
                "start": float(s.get("startMs", 0)) / 1000,
                "duration": (float(s.get("endMs", 0)) - float(s.get("startMs", 0))) / 1000,
            }
            for s in transcript
        ]
    return [
        {"text": s["text"], "start": float(s.get("start", 0)), "duration": float(s.get("duration", 0))}
        for s in transcript
    ]


def fetch_via_apify(video_id: str) -> list:
    """Fetch EN transcript via Apify only (APIFY_TOKEN required). No fallback."""
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise RuntimeError("APIFY_TOKEN not set in .env — required for transcript (YouTube blocks bots)")

    from apify_client import ApifyClient

    client = ApifyClient(token)
    url = f"https://www.youtube.com/watch?v={video_id}"
    base_input = {"urls": [{"url": url}], "outputFormat": "json", "languages": ["en"]}

    for actor_id, run_input in [
        ("curious_coder/youtube-transcript-scraper", base_input),
        ("scrape-creators/best-youtube-transcripts-scraper", {"videoUrls": [url]}),
    ]:
        try:
            run = client.actor(actor_id).call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            if not items:
                continue
            item = items[0]
            transcript = item.get("transcript") or []
            if transcript:
                return _normalize_segments(transcript)
        except Exception:
            continue

    raise RuntimeError("Apify: no actor returned transcript")


def main():
    if not sys.argv[1:]:
        print(json.dumps({"error": "Usage: fetch_transcript.py <video_id>"}), file=sys.stderr)
        sys.exit(1)
    video_id = sys.argv[1]

    try:
        result = fetch_via_apify(video_id)
        if result:
            print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
