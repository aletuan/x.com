#!/usr/bin/env python3
"""
Sync YouTube output folders: run summarize + translate for folders missing summary/timeline/VI.
Usage: python scripts/sync_youtube_outputs.py [--dry-run] [--skip-test]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS = PROJECT_ROOT / "skills" / "youtube-crawl-translate" / "scripts"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Print commands only")
    ap.add_argument("--skip-test", action="store_true", help="Skip test-video folder")
    args = ap.parse_args()

    output = PROJECT_ROOT / "output"
    to_summarize = []
    to_translate_summary = []
    to_translate_transcript = []

    for d in sorted(output.iterdir()):
        if not d.is_dir():
            continue
        meta_path = d / "metadata.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        if "video_id" not in meta:
            continue
        if args.skip_test and "test-video" in d.name:
            continue

        ov = len((meta.get("summary_overview") or "").strip())
        ov_vi = len((meta.get("summary_overview_vi") or "").strip())
        hl = len(meta.get("summary_highlights") or [])
        has_vi = (d / "transcript_vi.json").exists()

        if ov == 0 or hl == 0:
            to_summarize.append(d)
        elif ov > 0 and ov_vi == 0:
            to_translate_summary.append(d)

        if not has_vi and (d / "transcript.json").exists():
            to_translate_transcript.append(d)

    print(f"Summarize: {len(to_summarize)}|Translate summary: {len(to_translate_summary)}|Translate transcript: {len(to_translate_transcript)}", file=sys.stderr)

    for d in to_summarize:
        cmd = [sys.executable, str(SKILLS / "summarize_transcript.py"), "--output-dir", str(d)]
        if args.dry_run:
            print(" ".join(cmd))
        else:
            subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=True)

    for d in to_summarize + to_translate_summary:
        if d in to_summarize or (d / "metadata.json").read_text() and json.loads((d / "metadata.json").read_text()).get("summary_overview"):
            cmd = [sys.executable, str(SKILLS / "translate_summary.py"), "--output-dir", str(d)]
            if args.dry_run:
                print(" ".join(cmd))
            else:
                subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=True)

    for d in to_translate_transcript:
        cmd = [sys.executable, str(SKILLS / "translate_transcript.py"), "--output-dir", str(d)]
        if args.dry_run:
            print(f"cat {d}/transcript.json | {' '.join(cmd)}")
        else:
            with open(d / "transcript.json") as f:
                subprocess.run(cmd, stdin=f, cwd=str(PROJECT_ROOT), check=True)


if __name__ == "__main__":
    main()
