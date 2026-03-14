---
name: youtube-crawl-translate
description: Use when the user wants to crawl a YouTube video, get transcript with Vietnamese translation and summary. Output: HTML player with sync subtitles, dark mode, open in Cursor browser. Triggers on: crawl youtube, youtube transcript, dịch youtube, xem youtube có phụ đề.
---

# YouTube Crawl Translate

## Overview

Pipeline để crawl YouTube: lấy transcript (EN + VI qua Apify translateTo), tóm tắt chi tiết, tạo trang HTML với video embed + subtitle sync (toggle EN/VI, mặc định VI) + dark mode. Mở trong Cursor browser.

**Output:** `output/{slug}-{video_id}/player.html` — slug từ title (ví dụ: `steve-yegge-ai-agentic-coding-aFsAOu2bgFk`).

**Hướng dẫn chi tiết:** Xem [GUIDE.md](skills/youtube-crawl-translate/GUIDE.md) — Video ID là gì, cách lấy, lưu ý transcript bị chặn, ví dụ đầy đủ.

---

## Workflow — 5 Steps

| Step | Hành động | Tool / Cách |
|------|-----------|-------------|
| 1 | Parse video ID từ URL | Regex: `(?:youtube.com/watch\?v=|youtu.be/)([a-zA-Z0-9_-]{11})` |
| 2 | Fetch video info (title, output_dir) | `python skills/youtube-crawl-translate/scripts/fetch_video_info.py <video_id>` |
| 3 | Fetch transcript (EN + VI) | `python skills/youtube-crawl-translate/scripts/fetch_transcript.py <video_id>` |
| 4 | Summarize | Agent tóm tắt chi tiết với mốc thời gian và đoạn hội thoại ý nghĩa |
| 5 | Generate HTML + open | `generate_player.py` với `output_dir` từ step 2 |

---

## Chi tiết từng Step

### Step 1 — Parse video ID

```python
import re
url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # hoặc https://youtu.be/dQw4w9WgXcQ
match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
video_id = match.group(1) if match else None
```

### Step 2 — Fetch video info

Chạy từ project root để lấy title và output path có ý nghĩa:

```bash
python skills/youtube-crawl-translate/scripts/fetch_video_info.py <video_id>
```

Output: JSON `{"title": "...", "video_id": "...", "slug": "...", "output_dir": "output/{slug}-{video_id}"}`

Dùng `title` cho player, `output_dir` cho generate_player. Nếu không có API key → fallback `output/video-{video_id}`.

### Step 3 — Fetch transcript (EN + VI)

Chạy từ project root (X.com):

```bash
python skills/youtube-crawl-translate/scripts/fetch_transcript.py <video_id>
```

Script dùng Apify: lấy transcript tiếng Anh, thử `translateTo=vi` (YouTube built-in). Nếu không có kết quả → fallback `deep-translator` để dịch sang tiếng Việt.

Output: JSON array `[{"text": "...", "textVi": "...", "start": 0.0, "duration": 4.5}, ...]`

### Step 4 — Summarize

Dùng Cursor kết hợp transcript để tạo tóm tắt gồm **2 phần**:

**1. Mô tả tóm tắt** (`summary_overview`): **Chi tiết đủ để người đọc hiểu key content mà không cần xem video.** Không sơ sài. Gồm:
- Bối cảnh: ai, chủ đề, format (phỏng vấn, talk, v.v.)
- Luồng nội dung: các ý chính theo thứ tự, giải thích rõ từng khái niệm (ví dụ Gas Town là gì, vampiric effect là gì)
- Trích dẫn hoặc diễn giải các luận điểm quan trọng
- Kết luận, dự đoán, takeaway
- Độ dài: 15–25 câu (hoặc 200–400 từ), không chỉ liệt kê chủ đề.

**2. Danh sách đáng chú ý** (`summary_highlights`): Liệt kê các phần highlight trong video, mỗi mục gồm timestamp `[MM:SS]` và tóm tắt ngắn.

**Output JSON cho generate_player:**
```json
{
  "summary_overview": "Steve Yegge, kỹ sư 40 năm kinh nghiệm (Amazon, Google), tác giả Gas Town và Vibe Coding, trò chuyện về 8 levels AI adoption. Level 1: không dùng AI. Level 2: yes/no trong IDE. Level 6: agent làm việc, dev chờ — 'you're bored because your agent's busy'. Gas Town là nơi code cũ tích tụ, khó refactor. Vampiric effect: AI khiến dev làm việc cường độ cao, nap giữa ngày, nhưng output tổng thể không tăng tương xứng. Ông dự đoán big tech đang chết dần; team nhỏ 2–20 người có thể rival output. So sánh compilers (deterministic) vs LLMs (stochastic). CLI vs MCP: MCP cho tools tương tác với agent. 70% engineers vẫn ở levels thấp...",
  "summary_highlights": [
    "[00:08] Steve giải thích levels: Level 1 không AI, Level 6 'you're bored because your agent's busy'",
    "[08:48] \"What is Gas Town?\" — nơi code cũ tích tụ",
    "[15:22] Vampiric effect: AI hút sự chú ý, dev quên maintain code"
  ]
}
```

**Backward compat:** Nếu chỉ có `summary` (string), dùng làm overview.

### Step 5 — Generate HTML

Dùng `output_dir` và `title` từ fetch_video_info (step 2):

```bash
echo '{"video_id":"...","video_title":"...","transcript":[...],"summary_overview":"...","summary_highlights":["[00:08] ...","[05:32] ..."],"output_dir":"output/slug-video_id"}' | python skills/youtube-crawl-translate/scripts/generate_player.py
```

Sau đó mở trong browser: `open output/{slug}-{video_id}/player.html` hoặc HTTP server.

---

## Dependencies

- `pip install -r requirements.txt` (apify-client, deep-translator, python-dotenv)
- `.env` với `APIFY_TOKEN` (bắt buộc cho transcript — YouTube chặn bot, chỉ Apify hoạt động ổn định)

---

## Edge Cases

| Case | Xử lý |
|------|-------|
| Video không có transcript | Báo lỗi, bỏ qua; vẫn tạo player với summary |
| APIFY_TOKEN thiếu | Báo lỗi — cần token để lấy transcript (YouTube chặn bot) |
| Transcript ngôn ngữ khác | Apify translateTo=vi; nếu video không có phụ đề gốc → fallback tiếng Anh |

---

## Quick Reference

| Script | Input | Output |
|--------|-------|--------|
| fetch_video_info.py | video_id | JSON {title, slug, output_dir} |
| fetch_transcript.py | video_id | JSON transcript |
| generate_player.py | video_id, title, transcript, summary_overview, summary_highlights, output_dir | player.html |
