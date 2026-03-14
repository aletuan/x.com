#!/usr/bin/env python3
"""
Translate transcript EN→VI using Claude (batch, with progress).
Usage: cat transcript.json | python translate_transcript.py
   or: python translate_transcript.py < transcript.json
Output: JSON to stdout [{text, textVi, start, duration}, ...]
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

BATCH_SIZE = int(os.environ.get("YT_TRANSLATE_BATCH", "20"))
MODEL = os.environ.get("YT_TRANSLATE_MODEL", "claude-haiku-4-5-20251001")

SYSTEM_PROMPT = """You translate English transcript segments to Vietnamese.

Rules:
- Preserve conversational tone.
- Keep technical terms in English when standard (API, SaaS, Claude Code, Jira, etc.).
- Output exactly one Vietnamese line per input line, in the same order.
- No numbering, no extra text. Just the translations, one per line.
- If a line is [Music] or similar, output the same."""


def translate_batch(texts: list[str], client) -> list[str]:
    """Translate a batch of texts via Claude."""
    user_content = "\n".join(texts)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    block = resp.content[0]
    if block.type != "text":
        raise RuntimeError(f"Unexpected response type: {block.type}")
    out = block.text.strip().split("\n")
    # Pad or trim to match input count
    while len(out) < len(texts):
        out.append("")
    return out[: len(texts)]


def main():
    try:
        transcript = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}), file=sys.stderr)
        sys.exit(1)

    if not transcript or not isinstance(transcript, list):
        print(json.dumps({"error": "Empty or invalid transcript"}), file=sys.stderr)
        sys.exit(1)

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print(json.dumps({"error": "ANTHROPIC_API_KEY not set in .env"}), file=sys.stderr)
        sys.exit(1)

    from anthropic import Anthropic

    client = Anthropic()
    total = len(transcript)
    results = []

    for i in range(0, total, BATCH_SIZE):
        batch = transcript[i : i + BATCH_SIZE]
        texts = [s.get("text", "") or " " for s in batch]
        try:
            vi_texts = translate_batch(texts, client)
        except Exception as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            sys.exit(1)

        for j, seg in enumerate(batch):
            row = dict(seg)
            if j < len(vi_texts) and vi_texts[j]:
                row["textVi"] = vi_texts[j].strip()
            results.append(row)

        pct = min(100, int(100 * (i + len(batch)) / total))
        print(f"Translating... {pct}%", file=sys.stderr)

    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
