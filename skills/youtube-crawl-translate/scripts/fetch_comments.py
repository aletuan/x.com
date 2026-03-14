#!/usr/bin/env python3
"""
Fetch YouTube comments via Data API.
Usage: python fetch_comments.py <video_id>
Output: JSON to stdout
Requires: YOUTUBE_API_KEY in .env
"""
import json
import os
import sys
from pathlib import Path

# Load .env from project root
project_root = Path(__file__).resolve().parents[3]
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: fetch_comments.py <video_id>"}), file=sys.stderr)
        sys.exit(1)

    video_id = sys.argv[1]
    api_key = os.environ.get("YOUTUBE_API_KEY")

    if not api_key:
        print(json.dumps({"error": "YOUTUBE_API_KEY not set in .env", "comments": []}))
        return

    try:
        from googleapiclient.discovery import build

        youtube = build("youtube", "v3", developerKey=api_key)
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=50,
            order="relevance",
            textFormat="plainText",
        ).execute()

        comments = []
        for item in response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": snippet["authorDisplayName"],
                "text": snippet["textDisplay"],
                "likeCount": snippet.get("likeCount", 0),
                "publishedAt": snippet.get("publishedAt", ""),
            })

        print(json.dumps(comments, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e), "comments": []}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
