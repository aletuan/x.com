#!/usr/bin/env python3
"""
Fetch YouTube video metadata and compute semantic output path.
Usage: python fetch_video_info.py <video_id>
Output: JSON to stdout: {title, video_id, slug, output_dir, channel_title?, channel_id?, published_at?, duration?}
Requires: YOUTUBE_API_KEY in .env (fallback to video-{video_id} if missing)
"""
import json
import os
import re
import sys
from pathlib import Path

# Load .env from project root
project_root = Path(__file__).resolve().parents[3]
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)


def parse_iso_duration(duration_str: str) -> int:
    """Parse ISO 8601 duration (e.g. PT35M42S) to total seconds."""
    if not duration_str:
        return 0
    import re
    total = 0
    for m in re.finditer(r"(\d+)([HMS])", duration_str):
        val, unit = int(m.group(1)), m.group(2)
        if unit == "H":
            total += val * 3600
        elif unit == "M":
            total += val * 60
        elif unit == "S":
            total += val
    return total


def slugify(text: str, max_length: int = 60) -> str:
    """Create URL-safe slug from title: lowercase, spaces to hyphens, alphanumeric + hyphen."""
    if not text or not text.strip():
        return ""
    # Lowercase, replace non-alphanumeric with spaces
    s = re.sub(r"[^a-z0-9\s-]", "", text.lower().strip())
    # Collapse spaces/hyphens to single hyphen
    s = re.sub(r"[\s_-]+", "-", s)
    s = s.strip("-")
    return s[:max_length] if len(s) > max_length else s


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: fetch_video_info.py <video_id>"}), file=sys.stderr)
        sys.exit(1)

    video_id = sys.argv[1]
    api_key = os.environ.get("YOUTUBE_API_KEY")

    result = {"video_id": video_id, "title": "YouTube Video", "slug": f"video-{video_id}", "output_dir": f"output/video-{video_id}"}

    if api_key:
        try:
            from googleapiclient.discovery import build

            youtube = build("youtube", "v3", developerKey=api_key)
            response = youtube.videos().list(part="snippet,contentDetails", id=video_id).execute()
            items = response.get("items", [])
            if items:
                item = items[0]
                snippet = item.get("snippet", {})
                title = snippet.get("title", "YouTube Video")
                slug = slugify(title) or f"video-{video_id}"
                result["title"] = title
                result["slug"] = slug
                result["output_dir"] = f"output/{slug}-{video_id}"
                if snippet.get("channelTitle"):
                    result["channel_title"] = snippet["channelTitle"]
                if snippet.get("channelId"):
                    result["channel_id"] = snippet["channelId"]
                if snippet.get("publishedAt"):
                    result["published_at"] = snippet["publishedAt"]
                content = item.get("contentDetails", {})
                if content.get("duration"):
                    result["duration_seconds"] = parse_iso_duration(content["duration"])
        except Exception as e:
            result["error"] = str(e)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
