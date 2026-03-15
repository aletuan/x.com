#!/usr/bin/env python3
"""
Translate summary_overview EN→VI using Claude. Updates metadata.json in place.
Usage: python translate_summary.py --output-dir DIR
  --output-dir DIR: path to output folder (contains metadata.json)
Reads metadata.json, translates summary_overview to summary_overview_vi, writes back.
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

MODEL = os.environ.get("YT_TRANSLATE_MODEL", "claude-haiku-4-5-20251001")

SYSTEM_PROMPT = """You translate an English video summary to Vietnamese.

Rules:
- Preserve technical terms in English when standard (API, SaaS, MCP, RAG, LLM, etc.).
- Keep the same structure and level of detail.
- Output natural Vietnamese.
- Reply with the translated text only. No JSON wrapper, no markdown, no preamble."""


def main():
    parser = argparse.ArgumentParser(description="Translate summary EN→VI, update metadata.json")
    parser.add_argument(
        "--output-dir",
        "-o",
        metavar="DIR",
        required=True,
        help="Output folder containing metadata.json",
    )
    args = parser.parse_args()

    out_path = Path(args.output_dir)
    meta_path = out_path / "metadata.json"
    if not meta_path.exists():
        print(json.dumps({"error": f"metadata.json not found in {out_path}"}), file=sys.stderr)
        sys.exit(1)

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    overview = (meta.get("summary_overview") or "").strip()
    if not overview:
        print("No summary_overview to translate. Skipping.", file=sys.stderr)
        sys.exit(0)

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print(json.dumps({"error": "ANTHROPIC_API_KEY not set in .env"}), file=sys.stderr)
        sys.exit(1)

    from anthropic import Anthropic

    client = Anthropic()
    print("Translating summary...", file=sys.stderr)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Translate this video summary to Vietnamese:\n\n{overview}"}],
    )
    block = resp.content[0]
    if block.type != "text":
        raise RuntimeError(f"Unexpected response type: {block.type}")
    vi_text = block.text.strip()
    if not vi_text:
        print("Empty translation. Skipping.", file=sys.stderr)
        sys.exit(0)

    meta["summary_overview_vi"] = vi_text
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Done. summary_overview_vi updated in metadata.json. Refresh player to see.", file=sys.stderr)


if __name__ == "__main__":
    main()
