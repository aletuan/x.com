# X.com

Kho lưu trữ nội dung: YouTube crawl-translate (player + phụ đề EN/VI), bài viết dịch, blog nghiên cứu AI agents.

## Tính năng

- **YouTube crawl-translate** — Crawl video YouTube, lấy transcript, tóm tắt, dịch sang tiếng Việt, tạo player HTML có phụ đề đồng bộ
- **Article crawl-translate** — Crawl bài viết web, tải ảnh, dịch sang tiếng Việt
- **Blog** — Bài viết nghiên cứu về AI agents, leverage, MCP

## Quick start

```bash
# Chạy HTTP server để xem player
cd /path/to/X.com && python -m http.server 8765
```

Mở: `http://localhost:8765/player.html?dir=output/<thư-mục>`

## Cấu trúc

| Thư mục | Mô tả |
|---------|-------|
| [output/](./output/) | Kết quả crawl, dịch — YouTube player, bài viết |
| [blog/](./blog/) | Bài viết nghiên cứu AI agents |
| [skills/](./skills/) | Skills hướng dẫn agent (youtube-crawl-translate, article-crawl-translate) |
| [scripts/](./scripts/) | Script đồng bộ, sync outputs |

## Skills

| Skill | Mô tả |
|-------|-------|
| [youtube-crawl-translate](./skills/youtube-crawl-translate/) | Crawl YouTube, transcript EN/VI, player có phụ đề |
| [article-crawl-translate](./skills/article-crawl-translate/) | Crawl bài viết, dịch, lưu markdown |

## Yêu cầu

- Python 3
- [Apify](https://apify.com) (YouTube transcript)
- [Anthropic API](https://anthropic.com) (Claude — dịch, tóm tắt)
- `.env` với `APIFY_API_TOKEN`, `ANTHROPIC_API_KEY`

## License

MIT
