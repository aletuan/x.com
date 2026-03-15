#!/usr/bin/env python3
"""
Sync all YouTube output folders: add metadata.json and update player.html.
For folders with transcript.json, run generate_player.
For folders missing transcript, run fetch_transcript (Apify).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEO_ID_RE = re.compile(r'-([a-zA-Z0-9_-]{11})$')


def get_yt_folders():
    output = PROJECT_ROOT / "output"
    for d in output.iterdir():
        if not d.is_dir():
            continue
        if d.name in ("building-effective-agents", "code-execution-with-mcp"):
            continue
        m = VIDEO_ID_RE.search(d.name)
        if m:
            yield d, m.group(1)


def main():
    gen_script = PROJECT_ROOT / "skills/youtube-crawl-translate/scripts/generate_player.py"
    fetch_info = PROJECT_ROOT / "skills/youtube-crawl-translate/scripts/fetch_video_info.py"
    fetch_transcript = PROJECT_ROOT / "skills/youtube-crawl-translate/scripts/fetch_transcript.py"

    for folder, video_id in get_yt_folders():
        has_transcript = (folder / "transcript.json").exists()
        has_metadata = (folder / "metadata.json").exists()

        if not has_transcript:
            print(f"[SKIP] {folder.name}: no transcript.json - need to crawl")
            continue

        # Fetch video info
        r = subprocess.run(
            [sys.executable, str(fetch_info), video_id],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            print(f"[WARN] {folder.name}: fetch_video_info failed")
            continue
        try:
            info = json.loads(r.stdout)
        except json.JSONDecodeError:
            print(f"[WARN] {folder.name}: invalid fetch_video_info output")
            continue

        transcript = json.loads((folder / "transcript.json").read_text(encoding="utf-8"))
        payload = {
            "video_id": video_id,
            "video_title": info.get("title", "YouTube Video"),
            "output_dir": str(folder),
            "channel_title": info.get("channel_title", ""),
            "published_at": info.get("published_at", ""),
            "duration_seconds": info.get("duration_seconds"),
            "transcript": transcript,
            "summary_overview": "",
            "summary_highlights": [],
        }
        r2 = subprocess.run(
            [sys.executable, str(gen_script)],
            input=json.dumps(payload, ensure_ascii=False),
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
        )
        if r2.returncode == 0:
            print(f"[OK] {folder.name}")
        else:
            print(f"[FAIL] {folder.name}: {r2.stderr[:200]}")


if __name__ == "__main__":
    main()
