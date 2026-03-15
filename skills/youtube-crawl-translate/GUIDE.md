# Hướng dẫn YouTube Crawl Translate

## Video ID là gì?

**Video ID** là chuỗi 11 ký tự duy nhất của mỗi video YouTube, dùng để nhận diện video trong URL.

- **Định dạng:** `[a-zA-Z0-9_-]{11}` (chữ, số, gạch dưới, gạch ngang)
- **Ví dụ:** `dQw4w9WgXcQ`, `KQ6zr6kCPj8`, `9bZkp7q19f0`

---

## Cách lấy Video ID từ URL

### Từ URL dạng chuẩn

```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
                              └─────────────┘
                                   Video ID
```

### Từ URL rút gọn

```
https://youtu.be/dQw4w9WgXcQ
                 └─────────────┘
                      Video ID
```

### Parse bằng regex (Python)

```python
import re
url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # hoặc https://youtu.be/dQw4w9WgXcQ
match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
video_id = match.group(1) if match else None  # "dQw4w9WgXcQ"
```

### Bảng ví dụ URL → Video ID

| URL | Video ID |
|-----|----------|
| https://www.youtube.com/watch?v=dQw4w9WgXcQ | dQw4w9WgXcQ |
| https://youtu.be/dQw4w9WgXcQ | dQw4w9WgXcQ |
| https://www.youtube.com/watch?v=KQ6zr6kCPj8 | KQ6zr6kCPj8 |
| https://youtu.be/9bZkp7q19f0 | 9bZkp7q19f0 |

---

## Lưu ý quan trọng — Transcript

YouTube chặn bot (youtube-transcript-api, yt-dlp, Invidious thường thất bại). **Chỉ Apify hoạt động ổn định.**

### Cấu hình bắt buộc

Thêm vào `.env`:
```
APIFY_TOKEN=apify_api_xxxx
```

Script dùng Apify YouTube Transcript Scraper: `scrape-creators/best-youtube-transcripts-scraper` ($1/1000) hoặc `curious_coder/youtube-transcript-scraper` ($0.60/1000).

---

## YouTube bot detection — Nguyên nhân và giải pháp

### Vì sao YouTube chặn được bot

| Cơ chế | Mô tả |
|--------|-------|
| **Cloud IP blocking** | Chặn IP từ AWS, GCP, Azure, DigitalOcean — phát hiện qua IP range |
| **Rate limiting** | Giới hạn 2–3 request liên tiếp tới `/api/timedtext` trước khi block |
| **Anti-bot / CAPTCHA** | Trả `LOGIN_REQUIRED` — "Sign in to confirm you're not a bot" |
| **HTTP 429** | Too Many Requests, có thể kéo dài hàng giờ sau khi block |

Nguồn: [youtube-transcript-api issues](https://github.com/jdepoix/youtube-transcript-api/issues), [YT2Text blog](https://yt2text.cc/blog/youtube-transcript-api-best-practices)

### Giải pháp thay thế

| Giải pháp | Ưu | Nhược | Ghi chú |
|-----------|----|-------|---------|
| **Apify Actors** | Tỷ lệ thành công cao, proxy sẵn | Trả phí ~$0.60/1000 transcript | **Đang dùng** — `APIFY_TOKEN` trong .env |
| **Residential proxy** | Bypass cloud IP block | Tốn phí, cần cấu hình | Webshare, Bright Data |
| **YouTube Data API Captions** | API chính thức | Cần OAuth, chỉ cho video sở hữu | Không dùng cho video công khai |

### Đề xuất cho skill

1. **Chỉ dùng Apify** — youtube-transcript-api, yt-dlp, Invidious thường bị chặn bot
2. **Video hiển thị:** Dùng `host: youtube-nocookie.com`, mở qua HTTP server (cổng 8765) thay vì file://

---

## Ví dụ đầy đủ

### 1. Lấy Video ID

User cung cấp: `https://youtu.be/dQw4w9WgXcQ` → Video ID: `dQw4w9WgXcQ`

### 2. Fetch video info (title, output_dir)

```bash
python skills/youtube-crawl-translate/scripts/fetch_video_info.py dQw4w9WgXcQ
```

Output: `{"title":"Never Gonna Give You Up","output_dir":"output/never-gonna-give-you-up-dQw4w9WgXcQ",...}`

### 3. Fetch transcript

Truyền `output_dir` từ step 2 để lưu `transcript.json` cùng thư mục với player:

```bash
cd /Users/andy/X.com
python skills/youtube-crawl-translate/scripts/fetch_transcript.py dQw4w9WgXcQ output/never-gonna-give-you-up-dQw4w9WgXcQ
```

Output: JSON ra stdout và ghi vào `output/never-gonna-give-you-up-dQw4w9WgXcQ/transcript.json`

### 4. Tóm tắt (Agent)

Tóm tắt chi tiết với mốc thời gian `[MM:SS]` và các đoạn hội thoại ý nghĩa. Xem SKILL.md Step 4.

### 5. Generate player (Phase 1 — user xem ngay với EN)

Dùng `output_dir` từ fetch_video_info. Transcript EN: `[{text, start, duration}, ...]`.

```bash
echo '{"video_id":"dQw4w9WgXcQ","video_title":"Never Gonna Give You Up","transcript":[{"text":"Hi","start":0,"duration":1}],"summary_overview":"...","summary_highlights":["[00:00] ..."],"output_dir":"output/never-gonna-give-you-up-dQw4w9WgXcQ"}' | python skills/youtube-crawl-translate/scripts/generate_player.py
```

### 6. Mở player

HTTP server chạy từ **project root** (player dùng chung, load qua `?dir=`):
```bash
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
cd /Users/andy/X.com && python -m http.server 8765
# Mở http://localhost:8765/player.html?dir=output/never-gonna-give-you-up-dQw4w9WgXcQ
```

### 7. (Phase 2) Dịch VI — trong khi user xem

```bash
# Dịch transcript
cat output/never-gonna-give-you-up-dQw4w9WgXcQ/transcript.json | python skills/youtube-crawl-translate/scripts/translate_transcript.py --output-dir output/never-gonna-give-you-up-dQw4w9WgXcQ

# Dịch summary (cập nhật summary_overview_vi trong metadata.json)
python skills/youtube-crawl-translate/scripts/translate_summary.py --output-dir output/never-gonna-give-you-up-dQw4w9WgXcQ
```

Player tự load `transcript_vi.json` và `metadata.json` lúc runtime. User refresh trang để có phụ đề + tóm tắt tiếng Việt (không cần regenerate).

---

## Cấu trúc output

Folder dùng **slug từ title** + video_id. Player dùng chung ở project root (`player.html?dir=output/{folder}`):

```
output/
└── {slug}-{video_id}/
    ├── metadata.json       # video_id, title, summary, highlights
    ├── transcript.json     # EN (sau fetch_transcript)
    └── transcript_vi.json  # VI (sau translate_transcript)
```

**output/README.md:** Bảng YouTube **chỉ link tới player** (`http://localhost:8765/player.html?dir=output/{folder}`), không link tới folder. Script `update_output_index.py` (gọi từ generate_player) tự động thêm entry mới với link player.

Ví dụ: `output/how-to-code-with-ai-agents-advice-from-openclaw-creator-pete-wKy1_KLcxcs/`
