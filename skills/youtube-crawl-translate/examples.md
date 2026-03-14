# YouTube Crawl Translate — Examples

> **Hướng dẫn đầy đủ:** Xem [GUIDE.md](GUIDE.md) — Video ID, cách lấy, YouTube bot detection, lưu ý transcript bị chặn.

## URL mẫu

| URL | Video ID |
|-----|----------|
| https://www.youtube.com/watch?v=dQw4w9WgXcQ | dQw4w9WgXcQ |
| https://youtu.be/dQw4w9WgXcQ | dQw4w9WgXcQ |

## Lệnh mẫu

```bash
# Từ project root
cd /Users/andy/X.com

# 1. Fetch video info (title, output_dir có ý nghĩa)
python skills/youtube-crawl-translate/scripts/fetch_video_info.py dQw4w9WgXcQ
# → {"title":"Never Gonna Give You Up","output_dir":"output/never-gonna-give-you-up-dQw4w9WgXcQ",...}

# 2. Fetch transcript (ghi transcript.json vào output_dir)
python skills/youtube-crawl-translate/scripts/fetch_transcript.py dQw4w9WgXcQ output/never-gonna-give-you-up-dQw4w9WgXcQ

# 3. Generate (sau khi agent dịch + tóm tắt, dùng output_dir từ step 1)
echo '{"video_id":"dQw4w9WgXcQ","video_title":"Never Gonna Give You Up","transcript":[...],"summary":"...","output_dir":"output/never-gonna-give-you-up-dQw4w9WgXcQ"}' | python skills/youtube-crawl-translate/scripts/generate_player.py
```

## Output structure

Folder dùng slug từ title + video_id. Transcript luôn cùng thư mục với player:

```
output/
└── {slug}-{video_id}/
    ├── player.html
    ├── transcript.json      # EN
    └── transcript_vi.json   # VI (sau dịch)
```

Ví dụ: `output/how-to-code-with-ai-agents-advice-from-openclaw-creator-pete-wKy1_KLcxcs/`

## Transcript runtime

Player load `transcript_vi.json` (nếu có) hoặc `transcript.json` lúc runtime. Sau khi dịch xong, **refresh** trang để có phụ đề VI — không cần regenerate player.

## Mở player.html

Mở file trực tiếp trong browser: `open output/<slug>-<video_id>/player.html` (macOS) hoặc dùng HTTP server. Trước khi start, kill process đang chiếm cổng 8765:

```bash
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
cd output/<slug>-<video_id> && python -m http.server 8765
# Mở http://localhost:8765/player.html
```

## Transcript

**Bắt buộc:** Thêm `APIFY_TOKEN` vào `.env` — script chỉ dùng Apify (YouTube chặn bot).
