#!/usr/bin/env python3
"""
Translate transcript EN→VI using Claude (batch, with progress).
Usage: cat transcript.json | python translate_transcript.py [--output-dir DIR]
   or: python translate_transcript.py < transcript.json [--output-dir DIR]
  --output-dir DIR: write transcript_vi.json into DIR (same dir as player.html)
Output: JSON to stdout [{text, textVi, start, duration}, ...]
"""
import argparse
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
- Output EXACTLY one Vietnamese line per input line. Same count. Never merge or skip.
- Reply with a JSON array only: ["trans1", "trans2", ...] — no other text.
- If a line is [Music] or similar, output the same."""


def _sanitize_control_chars(s: str) -> str:
    """Replace control chars that break JSON parsing (Claude sometimes returns these in strings)."""
    import re
    return re.sub(r"[\x00-\x1f\x7f]", " ", s)


def _extract_json_array(raw: str):
    """Extract first valid JSON array from response (handles extra text, markdown)."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        if "control character" in str(e).lower() or "Invalid control" in str(e):
            try:
                return json.loads(_sanitize_control_chars(raw))
            except json.JSONDecodeError:
                pass
        if "Extra data" in str(e):
            # Response has valid JSON + trailing text: find first complete array
            depth, start, i = 0, -1, 0
            for i, c in enumerate(raw):
                if c == "[":
                    if depth == 0:
                        start = i
                    depth += 1
                elif c == "]":
                    depth -= 1
                    if depth == 0 and start >= 0:
                        return json.loads(raw[start : i + 1])
            raise RuntimeError("Could not extract JSON array from response") from e
        raise


def translate_batch(texts: list[str], client) -> list[str]:
    """Translate a batch of texts via Claude. Returns exactly len(texts) items."""
    user_content = f"Translate these {len(texts)} lines to Vietnamese. Reply with JSON array of {len(texts)} strings.\n\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
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
    out = _extract_json_array(raw)
    if not isinstance(out, list):
        raise RuntimeError("Expected JSON array")
    while len(out) < len(texts):
        out.append("")
    return [str(x).strip() if x else "" for x in out[: len(texts)]]


def main():
    parser = argparse.ArgumentParser(description="Translate transcript EN→VI")
    parser.add_argument(
        "--output-dir",
        "-o",
        metavar="DIR",
        help="Write transcript_vi.json into DIR (same dir as player.html)",
    )
    args = parser.parse_args()

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

    data = json.dumps(results, ensure_ascii=False)
    if args.output_dir:
        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "transcript_vi.json").write_text(data, encoding="utf-8")
    print(data)


if __name__ == "__main__":
    main()
