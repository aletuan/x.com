---
name: article-crawl-translate
description: Use when the user wants to crawl a web article, translate it to Vietnamese, download content images, and save as markdown with local image links. Triggers on: crawl article, save article, dịch bài viết, tải bài về.
---

# Article Crawl Translate

## Overview

Pipeline 5 bước để crawl bài viết web, tải ảnh về local, dịch sang tiếng Việt, và lưu markdown. Agent dùng tools có sẵn: `mcp_web_fetch`, `defuddle`, `curl`, file write. Không cần Python crawler.

**Quan hệ với defuddle:** defuddle chỉ extract markdown. Skill này thực hiện full pipeline (fetch → extract → images → translate → save). Có thể dùng defuddle cho bước extract khi cần.

---

## Quan trọng: Output của tools

| Tool | Output thực tế | Parse ảnh |
|------|----------------|------------|
| **mcp_web_fetch** | Markdown (đã convert từ HTML) | Chỉ nếu markdown có `![](url)` |
| **defuddle --json** | JSON với HTML + markdown | Parse HTML cho `<img src>` |
| **defuddle --md** | Markdown sạch | Parse `![](url)` trong markdown |

⚠️ **mcp_web_fetch KHÔNG trả HTML** — nó convert sang markdown. Nhiều trang (SPA, CSS background) có ảnh nhưng converter không xuất ra `![](url)`.

---

## Workflow — 5 Steps

| Step | Hành động | Tool / Cách |
|------|-----------|-------------|
| 1. Fetch | Lấy nội dung + nguồn để parse ảnh | `defuddle parse url --json` (ưu tiên) hoặc `mcp_web_fetch(url)` |
| 2. Extract | Lấy markdown + danh sách ảnh | Parse HTML (từ defuddle) HOẶC markdown (từ mcp_web_fetch) cho image URLs |
| 3. Download | Tải ảnh về local | `curl -L -o assets/img_N.ext "url"` |
| 4. Translate | Dịch nội dung sang tiếng Việt | Agent dịch trong context, giữ code blocks/URL |
| 5. Save | Ghi file markdown | Write `article.md` vào `output/{slug}/` |

---

## Chi tiết từng Step

### Step 1 — Fetch

**Ưu tiên khi cần ảnh:**
1. **defuddle** (nếu đã cài): `defuddle parse <url> --json` → lấy HTML + markdown. HTML để parse `<img src>`.
2. **mcp_web_fetch**: Lấy markdown. Kiểm tra output có `![](url)` không — nếu không có, ảnh có thể bị mất.

**Chỉ cần text:** `mcp_web_fetch` hoặc `defuddle parse <url> --md` đủ.

### Step 2 — Extract

**Markdown:** Dùng từ defuddle `--md` hoặc từ mcp_web_fetch.

**Danh sách ảnh — 2 nguồn:**

| Nguồn | Cách extract |
|-------|--------------|
| **HTML** (defuddle --json) | Regex: `<img[^>]+(?:src|data-src)=["']([^"']+)["']` trong main content. Ưu tiên `data-src` nếu có (lazy-load). |
| **Markdown** (mcp_web_fetch / defuddle --md) | Regex: `!\[[^\]]*\]\((https?://[^)]+)\)` — lấy URL trong `![](url)`. |

**Loại trừ:** data URI (`data:image/...`), icon nhỏ (width/height < 100), ảnh OG/social. Chuyển relative URL → absolute. Giữ thứ tự xuất hiện.

**Fallback khi không có ảnh:** Nếu trang có ảnh (user xác nhận hoặc trang SPA/JS nặng) nhưng fetch không trả về — dùng **Browser MCP** (user-playwright): `browser_navigate` → `browser_evaluate` với:

```js
() => {
  const article = document.querySelector('article');
  const imgs = article ? article.querySelectorAll('img') : document.querySelectorAll('img');
  return Array.from(imgs).map(i => ({ src: i.src || i.dataset.src, w: i.naturalWidth, h: i.naturalHeight }))
    .filter(x => x.src && !x.src.startsWith('data:') && (x.w > 100 || x.h > 100));
}
```

Scope vào `article` để tránh ảnh nav/footer. Lọc ảnh nhỏ (w/h < 100) để bỏ icon.

### Step 3 — Download

- Tạo folder `output/{slug}/assets/`. Slug = tên thư mục từ URL (ví dụ: `building-effective-agents`).
- Với mỗi URL ảnh: `curl -L -o output/{slug}/assets/img_01.png "https://..."`
- Đặt tên: `img_01.png`, `img_02.png`, … theo thứ tự. Giữ extension gốc (.png, .jpg, .webp).
- `-L` để follow redirect.

### Step 4 — Translate

- Agent dịch toàn bộ markdown sang tiếng Việt.
- **Giữ nguyên:** code blocks (```...```), URL trong text, cấu trúc heading/list.
- **Thay thế:** `![](original_url)` → `![](assets/img_N.png)` (path local).
- Alt text ảnh: có thể dịch nếu phù hợp ngữ cảnh.

### Step 5 — Save

- Ghi `output/{slug}/article.md` với YAML frontmatter:

```yaml
---
title: "[Tiêu đề đã dịch]"
source_url: "https://..."
translated_at: "YYYY-MM-DD"
lang: vi
---
```

- Cấu trúc output:
  - `output/{slug}/article.md`
  - `output/{slug}/assets/img_01.png`, `img_02.png`, …

---

## Output Format Template

```markdown
---
title: "[Tiêu đề đã dịch]"
source_url: "https://..."
translated_at: "YYYY-MM-DD"
lang: vi
---

# [Tiêu đề đã dịch]

[Nội dung đã dịch, giữ cấu trúc heading/list/code]

![Mô tả](assets/img_01.png)
```

---

## Edge Cases

| Case | Hướng dẫn |
|------|-----------|
| Ảnh lazy-load (`data-src`) | Parse cả `src` và `data-src`, ưu tiên `data-src` nếu có |
| URL relative | Resolve với base URL (scheme + host + path của trang) |
| mcp_web_fetch không có ảnh | Fallback: defuddle --json (parse HTML) hoặc Browser MCP (evaluate `document.querySelectorAll('img')`) |
| Ảnh nhúng CSS/SVG/Canvas | Không extract được bằng img tag — thông báo user, trang có thể cần screenshot thủ công |
| Site chặn fetch (Cloudflare) | curl thường bị chặn; mcp_web_fetch hoặc defuddle có thể qua được. Nếu không: dùng Browser MCP |
| Ảnh lỗi 404 | Bỏ qua, giữ link gốc trong markdown hoặc ghi chú |

---

## Quick Reference

| Tool | Output | Dùng khi |
|------|---------|----------|
| defuddle parse url --json | HTML + markdown | **Ưu tiên** khi cần ảnh — parse HTML cho `<img>` |
| defuddle parse url --md | Markdown | Extract nhanh, parse `![](url)` nếu có |
| mcp_web_fetch | Markdown | Khi defuddle chưa cài; parse `![](url)` nếu có |
| Browser MCP (navigate + evaluate) | DOM / image URLs | Fallback khi fetch không có ảnh, trang SPA |
| curl -L -o path "url" | File | Tải ảnh |
| Write file | — | Ghi article.md |

---

## Common Mistakes

| Sai | Đúng |
|-----|------|
| Quên resolve relative URL | Luôn resolve với base URL trước khi download |
| Quên tạo folder assets/ | Tạo `output/{slug}/assets/` trước khi curl |
| Dùng path tuyệt đối trong markdown | Dùng path tương đối `assets/img_01.png` |
| Dịch code blocks | Giữ nguyên code blocks |
| Bỏ qua data-src | Kiểm tra cả src và data-src cho lazy-load |

---

## Dependencies

- **curl:** Có sẵn trên macOS/Linux.
- **defuddle (khuyến nghị):** `npm install -g defuddle-cli` — cho extract HTML + ảnh tốt hơn mcp_web_fetch.
- **Browser MCP** (Playwright / cursor-ide-browser): Fallback khi cần ảnh từ trang SPA/JS nặng.
