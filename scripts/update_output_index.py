#!/usr/bin/env python3
"""
Update output/README.md with new crawl entry. Idempotent — skips if entry exists.
Called by article-crawl-translate (Step 6) and youtube-crawl-translate (after generate_player).

Usage:
  python scripts/update_output_index.py --type article --output-dir output/slug [--title "Title"]
  python scripts/update_output_index.py --type youtube --output-dir output/slug-video_id --title "Video title"

Run from project root (X.com).
"""
import argparse
import re
import sys
from pathlib import Path


README_PATH = Path(__file__).resolve().parent.parent / "output" / "README.md"


def slug_from_output_dir(output_dir: str) -> str:
    """Extract folder name from output_dir (e.g. output/foo-bar -> foo-bar)."""
    return Path(output_dir).name


def read_title_from_article(output_dir: Path) -> str | None:
    """Read title from article.md frontmatter."""
    article = output_dir / "article.md"
    if not article.exists():
        return None
    text = article.read_text(encoding="utf-8")
    m = re.search(r'^title:\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    return m.group(1).strip() if m else None


def parse_table_section(content: str, section_header: str) -> tuple[list[str], int]:
    """
    Find table in section, return (data_rows, last_row_line_index).
    """
    lines = content.split("\n")
    in_section = False
    rows = []
    last_idx = -1

    for i, line in enumerate(lines):
        if line.strip().startswith(section_header):
            in_section = True
            continue
        if in_section:
            if line.strip().startswith("### "):
                break
            stripped = line.strip()
            if stripped.startswith("|") and "---" not in stripped:
                if re.match(r"^\|\s*\d+\s*\|", stripped):
                    rows.append(line)
                    last_idx = i

    return rows, last_idx


def extract_folder_from_row(row: str, entry_type: str = "article") -> str | None:
    """Extract folder from markdown link. Article: [text](./folder/article.md). YouTube: [text](...?dir=output/folder)."""
    if entry_type == "youtube":
        m = re.search(r"dir=output/([^\"'\s)]+)", row)
        return m.group(1) if m else None
    m = re.search(r'\]\(\./([^/)]+)(?:/|/article\.md)?\)', row)
    return m.group(1) if m else None


def escape_table_cell(s: str) -> str:
    """Escape | in table cell to avoid breaking markdown."""
    return s.replace("|", "\\|")


def add_entry_to_readme(
    readme_path: Path,
    entry_type: str,
    folder: str,
    title: str,
) -> bool:
    """
    Add new entry to README. Returns True if added, False if already exists.
    """
    content = readme_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    title_esc = escape_table_cell(title)

    if entry_type == "article":
        section = "### Bài viết (article)"
        link = f"[{folder}](./{folder}/article.md)"
        new_row = f"| {{n}} | {link} | {title_esc} |"
    else:
        section = "### YouTube (player + transcript EN/VI)"
        player_url = f"http://localhost:8765/player.html?dir=output/{folder}"
        link = f"[{title_esc}]({player_url})"
        new_row = f"| {{n}} | {link} |"

    rows, last_idx = parse_table_section(content, section)
    if last_idx < 0:
        return False

    existing_folders = set()
    for r in rows:
        f = extract_folder_from_row(r, entry_type)
        if f:
            existing_folders.add(f)

    if folder in existing_folders:
        return False

    next_n = len(rows) + 1
    new_row = new_row.format(n=next_n)

    insert_idx = last_idx + 1
    lines.insert(insert_idx, new_row)

    readme_path.write_text("\n".join(lines), encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="Update output/README.md with new crawl entry")
    parser.add_argument("--type", choices=["article", "youtube"], required=True)
    parser.add_argument("--output-dir", required=True, help="e.g. output/slug or output/slug-video_id")
    parser.add_argument("--title", help="Display title (for article, reads from frontmatter if omitted)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        output_dir = project_root / args.output_dir

    folder = slug_from_output_dir(str(output_dir))

    if args.type == "article":
        title = args.title or read_title_from_article(output_dir)
        if not title:
            print("Could not determine title (--title or article.md frontmatter)", file=sys.stderr)
            return 1
    else:
        title = args.title or folder.replace("-", " ").title()
        if not title:
            return 1

    if not README_PATH.exists():
        print(f"README not found: {README_PATH}", file=sys.stderr)
        return 1

    added = add_entry_to_readme(README_PATH, args.type, folder, title)
    if added:
        print(f"Updated output/README.md: added {args.type} {folder}")
    else:
        print(f"output/README.md: entry for {folder} already exists, skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
