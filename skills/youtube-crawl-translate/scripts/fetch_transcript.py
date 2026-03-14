#!/usr/bin/env python3
"""
Fetch YouTube transcript (EN + VI) via Apify.
Uses curious_coder/youtube-transcript-scraper: EN transcript + translateTo=vi.
Usage: python fetch_transcript.py <video_id>
Output: JSON to stdout [{text, textVi, start, duration}, ...]
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
    """Fetch EN + VI transcript via Apify (APIFY_TOKEN required)."""
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise RuntimeError("APIFY_TOKEN not set in .env — required for transcript (YouTube blocks bots)")

    from apify_client import ApifyClient

    client = ApifyClient(token)
    url = f"https://www.youtube.com/watch?v={video_id}"
    base_input = {"urls": [{"url": url}], "outputFormat": "json", "languages": ["en"]}

    # 1. Fetch English transcript
    en_segments = None
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
                en_segments = _normalize_segments(transcript)
                break
        except Exception:
            continue
    if not en_segments:
        raise RuntimeError("Apify: no actor returned transcript")

    # 2. Fetch Vietnamese: Apify translateTo (curious_coder) or googletrans fallback
    vi_segments = None
    try:
        run = client.actor("curious_coder/youtube-transcript-scraper").call(
            run_input={**base_input, "translateTo": "vi"}
        )
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        if items:
            transcript = items[0].get("transcript") or []
            if transcript:
                vi_segments = _normalize_segments(transcript)
    except Exception as e:
        print(json.dumps({"warn": f"Apify translateTo=vi failed: {e}"}), file=sys.stderr)

    if not vi_segments and en_segments:
        try:
            from deep_translator import GoogleTranslator
            trans = GoogleTranslator(source="auto", target="vi")
            vi_texts = []
            max_segments = int(os.environ.get("YT_TRANSLATE_MAX", "2000"))
            to_translate = en_segments[:max_segments]
            chunk_size = 30
            for i in range(0, len(to_translate), chunk_size):
                chunk = [s["text"][:500] or " " for s in to_translate[i : i + chunk_size]]
                batch = trans.translate_batch(chunk)
                vi_texts.extend([(t or "").strip() for t in batch])
            if len(vi_texts) == len(to_translate):
                vi_segments = [
                    {"text": vi_texts[j], "start": s["start"], "duration": s["duration"]}
                    for j, s in enumerate(to_translate)
                ]
        except Exception as e:
            print(json.dumps({"warn": f"deep-translator fallback failed: {e}", "hint": "pip install deep-translator"}), file=sys.stderr)

    # 3. Merge: align by index first; if counts differ, match by start time
    def find_vi_text(en_start: float) -> str | None:
        if not vi_segments:
            return None
        for vs in vi_segments:
            if abs(vs["start"] - en_start) < 0.5:
                return vs["text"] or None
        return None

    out = []
    for i, seg in enumerate(en_segments):
        row = {"text": seg["text"], "start": seg["start"], "duration": seg["duration"]}
        vi_text = None
        if vi_segments and i < len(vi_segments) and vi_segments[i].get("text"):
            vi_text = vi_segments[i]["text"]
        if not vi_text:
            vi_text = find_vi_text(seg["start"])
        if vi_text:
            row["textVi"] = vi_text
        out.append(row)
    return out


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
