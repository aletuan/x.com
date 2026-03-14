---
name: youtube-crawl-translate
description: Use when the user wants to crawl a YouTube video, get transcript and summary. Output: HTML player with sync subtitles, dark mode, open in Cursor browser. Triggers on: crawl youtube, youtube transcript, dịch youtube, xem youtube có phụ đề.
---

# YouTube Crawl Translate

## Overview

Pipeline **progressive**: lấy transcript EN từ Apify → tóm tắt → generate player → **mở ngay** (user xem với EN). Dịch VI chạy **background**, regenerate player khi xong (user refresh để có VI).

**Quan trọng:** Chỉ dùng transcript từ Apify. **Không fallback web fetch** — nếu Apify fail thì báo lỗi, không tạo player.

**Output:** `output/{slug}-{video_id}/` chứa `player.html`, `transcript.json` (EN), `transcript_vi.json` (sau dịch). Sau khi generate player, script tự động cập nhật `output/README.md`.

**Hướng dẫn chi tiết:** Xem [GUIDE.md](skills/youtube-crawl-translate/GUIDE.md) — Video ID là gì, cách lấy, lưu ý transcript bị chặn, ví dụ đầy đủ.

---

## Workflow — Progressive (UX tối ưu)

**Phase 1 (nhanh):** User xem ngay với EN

| Step | Hành động | Tool / Cách |
|------|-----------|-------------|
| 1 | Parse video ID từ URL | Regex: `(?:youtube.com/watch\?v=|youtu.be/)([a-zA-Z0-9_-]{11})` |
| 2 | Fetch video info (title, output_dir) | `python skills/youtube-crawl-translate/scripts/fetch_video_info.py <video_id>` |
| 3 | Fetch transcript (EN, Apify only) | `python .../fetch_transcript.py <video_id> <output_dir>` — ghi `transcript.json` vào output_dir |
| 4 | Summarize | Agent tóm tắt chi tiết với mốc thời gian và đoạn hội thoại ý nghĩa |
| 5 | Generate HTML + open | `generate_player.py` với transcript EN → Mở browser |

**Phase 2 (background):** Trong khi user xem, dịch VI rồi regenerate

| Step | Hành động | Tool / Cách |
|------|-----------|-------------|
| 6 | Dịch EN→VI (Claude) | `cat output_dir/transcript.json \| translate_transcript.py --output-dir output_dir` — ghi `transcript_vi.json` |
| 7 | (Không cần regenerate) | Player load `transcript_vi.json` lúc runtime → User **refresh** trang để có phụ đề VI |

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

### Step 3 — Fetch transcript (EN, Apify only)

Chạy từ project root (X.com). Truyền `output_dir` từ step 2 để lưu `transcript.json` cùng thư mục với player:

```bash
python skills/youtube-crawl-translate/scripts/fetch_transcript.py <video_id> <output_dir>
```

Ví dụ: `output_dir=output/how-to-code-with-ai-agents-wKy1_KLcxcs` → ghi `transcript.json` vào đó.

Script **chỉ dùng Apify** — 1 run lấy transcript tiếng Anh (nhanh nhất). Không fallback web fetch, không dịch VI.

Output: JSON array ra stdout (và ghi vào `output_dir/transcript.json`)

**Nếu Apify fail:** Báo lỗi, dừng pipeline. Không tạo player với transcript giả/fallback.

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

### Step 5 — Generate HTML (Phase 1)

Dùng `output_dir` và `title` từ fetch_video_info (step 2). Transcript EN only — user xem ngay:

```bash
echo '{"video_id":"...","video_title":"...","transcript":[...],"summary_overview":"...","summary_highlights":["[00:08] ...","[05:32] ..."],"output_dir":"output/slug-video_id"}' | python skills/youtube-crawl-translate/scripts/generate_player.py
```

Sau đó mở trong browser: `open output/{slug}-{video_id}/player.html` hoặc HTTP server.

**Mở HTTP server (cổng 8765 — ít conflict hơn 8080):** Trước khi start, kill process đang chiếm cổng:
```bash
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
cd output/{slug}-{video_id} && python -m http.server 8765
# Mở http://localhost:8765/player.html
```

### Step 6–7 — (Phase 2) Dịch VI + Regenerate

**Trong khi user đang xem**, chạy dịch trong background:

```bash
# Step 6: Dịch (từ transcript.json trong output_dir) — ghi transcript_vi.json vào cùng thư mục
cat output_dir/transcript.json | python skills/youtube-crawl-translate/scripts/translate_transcript.py --output-dir output_dir
# Không dùng 2>&1 — sẽ trộn progress vào file
```

**Không cần regenerate player.** Player tự load `transcript_vi.json` lúc runtime (ưu tiên hơn `transcript.json`). User refresh trang để có phụ đề tiếng Việt.

Cần `ANTHROPIC_API_KEY` trong `.env`. User refresh trang để có phụ đề tiếng Việt.

---

## Dependencies

- `pip install -r requirements.txt` (apify-client, anthropic, python-dotenv)
- `.env`:
  - `APIFY_TOKEN` (bắt buộc cho transcript)
  - `ANTHROPIC_API_KEY` (cho dịch VI — Phase 2)

---

## Edge Cases

| Case | Xử lý |
|------|-------|
| Apify fail / timeout | Báo lỗi, dừng pipeline. **Không** fallback web fetch |
| Video không có transcript | Báo lỗi — Apify không trả về transcript |
| APIFY_TOKEN thiếu | Báo lỗi — cần token để lấy transcript (YouTube chặn bot) |

---

## Quick Reference

| Script | Input | Output |
|--------|-------|--------|
| fetch_video_info.py | video_id | JSON {title, slug, output_dir} |
| fetch_transcript.py | video_id | JSON transcript (EN) |
| fetch_transcript.py | video_id, output_dir | + ghi transcript.json vào output_dir |
| translate_transcript.py | transcript JSON (stdin) | transcript với textVi |
| translate_transcript.py | transcript (stdin), --output-dir | + ghi transcript_vi.json vào output_dir |
| generate_player.py | video_id, title, transcript, summary_overview, summary_highlights, output_dir | player.html |
