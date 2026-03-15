---
name: youtube-crawl-translate
description: Use when the user wants to crawl a YouTube video, get transcript and summary. Output: HTML player with sync subtitles, dark mode, open in Cursor browser. Triggers on: crawl youtube, youtube transcript, dịch youtube, xem youtube có phụ đề.
---

# YouTube Crawl Translate

## Overview

Pipeline **progressive**: lấy transcript EN từ Apify → tóm tắt → generate player → **mở ngay** (user xem với EN). Dịch VI chạy **background**, regenerate player khi xong (user refresh để có VI).

**Quan trọng:** Chỉ dùng transcript từ Apify. **Không fallback web fetch** — nếu Apify fail thì báo lỗi, không tạo player.

**Output:** `output/{slug}-{video_id}/` chứa `metadata.json`, `transcript.json` (EN), `transcript_vi.json` (sau dịch). Player dùng chung ở root: `player.html?dir=output/{folder}`. Sau khi generate, script tự động cập nhật `output/README.md` — **chỉ link tới player**, không link tới folder.

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

**Phase 2 (background):** Trong khi user xem, dịch VI

| Step | Hành động | Tool / Cách |
|------|-----------|-------------|
| 6a | Dịch transcript EN→VI | `cat output_dir/transcript.json \| translate_transcript.py --output-dir output_dir` — ghi `transcript_vi.json` |
| 6b | Dịch summary EN→VI | `python translate_summary.py --output-dir output_dir` — cập nhật `summary_overview_vi` trong metadata.json |
| 7 | (Không cần regenerate) | Player load `transcript_vi.json` + metadata.json lúc runtime → User **refresh** trang để có phụ đề + tóm tắt VI |

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

**1. Mô tả tóm tắt** (`summary_overview`):
- **Mục tiêu:** Người đọc hiểu nội dung chính mà không cần xem video.
- **Cấu trúc:**
  - Mở (2–3 câu): Ai nói, chủ đề gì, format (talk/interview). Câu hook.
  - Thân: Các ý chính theo thứ tự. Giải thích thuật ngữ lần đầu (ví dụ: MCP = Model Context Protocol).
  - Kết: Takeaway, dự đoán.
- **Phong cách:** Viết trực tiếp, tránh "The speaker says/lays out/argues...". Ưu tiên nội dung hơn meta.
- **Độ dài:** 15–25 câu (200–400 từ).
- **Liệt kê:** Xuống dòng, mỗi mục bắt đầu bằng `- ` (gạch đầu dòng). Không dùng (1), (2), (3)... — player render thành `<ul><li>`. Ví dụ:
  ```
  Bốn công cụ: (dòng trống)
  - System prompt — cân bằng vague vs prescriptive...
  - Tool descriptions — cụ thể, có schema...
  - Data retrieval — RAG vs MCP...
  - Long-horizon — compaction, memory, composition
  ```
- **Tránh:** Liệt kê chủ đề, câu chung chung, lặp giữa overview và highlights.

**2. Danh sách đáng chú ý** (`summary_highlights`):
- Mỗi mục: `[MM:SS]` + tóm tắt ngắn (≤15 từ).
- Phân bố 5–12 mục đều theo thời gian video.
- Mix: định nghĩa, trích dẫn, insight hành động, câu hỏi nổi bật.
- Tránh: Nhiều mục chỉ là topic header giống nhau.

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

Sau đó mở player (HTTP server chạy từ **project root**):
```bash
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
cd /path/to/X.com && python -m http.server 8765
# Mở http://localhost:8765/player.html?dir=output/{slug}-{video_id}
```

### Step 6–7 — (Phase 2) Dịch VI

**Trong khi user đang xem**, chạy dịch trong background:

```bash
# Step 6a: Dịch transcript — ghi transcript_vi.json
cat output_dir/transcript.json | python skills/youtube-crawl-translate/scripts/translate_transcript.py --output-dir output_dir

# Step 6b: Dịch summary — cập nhật summary_overview_vi trong metadata.json
python skills/youtube-crawl-translate/scripts/translate_summary.py --output-dir output_dir
```

**Không cần regenerate player.** Player load `transcript_vi.json` và `metadata.json` lúc runtime. User refresh trang để có phụ đề + tóm tắt tiếng Việt.

Cần `ANTHROPIC_API_KEY` trong `.env`.

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
| summarize_transcript.py | --output-dir | đọc transcript.json, tạo summary_overview + summary_highlights, cập nhật metadata.json |
| fetch_transcript.py | video_id, output_dir | + ghi transcript.json vào output_dir |
| translate_transcript.py | transcript JSON (stdin) | transcript với textVi |
| translate_transcript.py | transcript (stdin), --output-dir | + ghi transcript_vi.json vào output_dir |
| translate_summary.py | --output-dir | đọc metadata.json, dịch summary_overview → summary_overview_vi, ghi lại metadata.json |
| generate_player.py | video_id, title, transcript, summary_overview, summary_highlights, output_dir | metadata.json + cập nhật output/README (link player) |
