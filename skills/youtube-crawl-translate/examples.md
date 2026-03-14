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

# 2. Fetch transcript
python skills/youtube-crawl-translate/scripts/fetch_transcript.py dQw4w9WgXcQ

# 3. Generate (sau khi agent dịch + tóm tắt, dùng output_dir từ step 1)
echo '{"video_id":"dQw4w9WgXcQ","video_title":"Never Gonna Give You Up","transcript":[...],"summary":"...","output_dir":"output/never-gonna-give-you-up-dQw4w9WgXcQ"}' | python skills/youtube-crawl-translate/scripts/generate_player.py
```

## Output structure

Folder dùng slug từ title + video_id:

```
output/
└── {slug}-{video_id}/
    └── player.html
```

Ví dụ: `output/steve-yegge-ai-agentic-coding-aFsAOu2bgFk/player.html`

## Mở player.html

Mở file trực tiếp trong browser: `open output/<slug>-<video_id>/player.html` (macOS) hoặc dùng HTTP server:

```bash
cd output/<slug>-<video_id> && python -m http.server 8080
# Mở http://localhost:8080/player.html
```

## Transcript

**Bắt buộc:** Thêm `APIFY_TOKEN` vào `.env` — script chỉ dùng Apify (YouTube chặn bot).
