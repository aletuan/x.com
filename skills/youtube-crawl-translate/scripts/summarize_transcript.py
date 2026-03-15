#!/usr/bin/env python3
"""
Summarize transcript using Claude. Updates metadata.json with summary_overview and summary_highlights.
Usage: python summarize_transcript.py --output-dir DIR

Reads transcript.json and metadata.json, generates summary per SKILL prompt, writes back.
"""
import argparse
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

MODEL = os.environ.get("YT_SUMMARIZE_MODEL", "claude-sonnet-4-20250514")


def format_ts(sec: float) -> str:
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m}:{s:02d}"


def transcript_to_text(segments: list) -> str:
    """Convert transcript segments to readable text with timestamps."""
    lines = []
    for s in segments:
        start = s.get("start", 0)
        text = (s.get("text") or "").strip()
        if text:
            lines.append(f"[{format_ts(start)}] {text}")
    return "\n".join(lines)


SYSTEM_PROMPT = """You summarize a YouTube video transcript. Output valid JSON only, no markdown, no preamble.

Output format:
{
  "summary_overview": "string (200-400 words)",
  "summary_highlights": ["[MM:SS] short description", ...]
}

Rules for summary_overview:
- Goal: reader understands main content without watching.
- Structure: opening (who, topic, format), body (main points in order), closing (takeaway).
- Style: direct, avoid "The speaker says/argues...". Prioritize content over meta.
- Length: 15-25 sentences (200-400 words).
- Lists: use "- " bullet, no (1),(2),(3) — player renders as <ul><li>.
- Explain terms on first use (e.g. MCP = Model Context Protocol).
- Avoid: topic lists, generic sentences, repetition with highlights.

Rules for summary_highlights:
- Each item: [MM:SS] + short summary (≤15 words).
- 5-12 items, evenly distributed across video timeline.
- Mix: definitions, quotes, action insights, notable questions.
- Avoid: many items that are just topic headers."""


def main():
    parser = argparse.ArgumentParser(description="Summarize transcript, update metadata.json")
    parser.add_argument("--output-dir", "-o", metavar="DIR", required=True, help="Output folder")
    args = parser.parse_args()

    out_path = Path(args.output_dir)
    meta_path = out_path / "metadata.json"
    transcript_path = out_path / "transcript.json"

    if not meta_path.exists():
        print(json.dumps({"error": f"metadata.json not found in {out_path}"}), file=sys.stderr)
        sys.exit(1)
    if not transcript_path.exists():
        print(json.dumps({"error": f"transcript.json not found in {out_path}"}), file=sys.stderr)
        sys.exit(1)

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    if not isinstance(transcript, list) or len(transcript) == 0:
        print(json.dumps({"error": "Empty or invalid transcript"}), file=sys.stderr)
        sys.exit(1)

    video_title = meta.get("video_title", "YouTube Video")
    channel_title = meta.get("channel_title", "")
    transcript_text = transcript_to_text(transcript)

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print(json.dumps({"error": "ANTHROPIC_API_KEY not set in .env"}), file=sys.stderr)
        sys.exit(1)

    from anthropic import Anthropic

    user_content = f"""Video: {video_title}
Channel: {channel_title}

Transcript (with timestamps):
---
{transcript_text}
---

Generate summary_overview and summary_highlights. Output JSON only."""

    print("Summarizing transcript...", file=sys.stderr)
    client = Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    block = resp.content[0]
    if block.type != "text":
        raise RuntimeError(f"Unexpected response type: {block.type}")

    raw = block.text.strip()
    # Strip markdown code block if present
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON from model: {e}", file=sys.stderr)
        print(raw[:500], file=sys.stderr)
        sys.exit(1)

    overview = (result.get("summary_overview") or "").strip()
    highlights = result.get("summary_highlights") or []
    if not isinstance(highlights, list):
        highlights = [h.strip() for h in str(highlights).split("\n") if h.strip()]

    meta["summary_overview"] = overview
    meta["summary_overview_vi"] = meta.get("summary_overview_vi") or ""
    meta["summary_highlights"] = highlights
    meta["num_events"] = len(highlights)

    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Done. summary_overview ({len(overview)} chars), {len(highlights)} highlights.", file=sys.stderr)


if __name__ == "__main__":
    main()
