# Article Crawl Translate — Examples

## URL mẫu

| URL | Mô tả |
|-----|-------|
| https://www.anthropic.com/engineering/building-effective-agents | Bài Anthropic về building agents |
| https://www.anthropic.com/news/model-context-protocol | MCP announcement |

## Output mẫu

**Input:** `Crawl https://www.anthropic.com/engineering/building-effective-agents và dịch sang tiếng Việt`

**Output structure:**
```
output/
└── building-effective-agents/
    ├── article.md
    └── assets/
        ├── img_01.png
        ├── img_02.png
        └── img_03.png
```

**article.md (đầu file):**
```markdown
---
title: "Xây dựng agent hiệu quả"
source_url: "https://www.anthropic.com/engineering/building-effective-agents"
translated_at: "2026-03-13"
lang: vi
---

# Xây dựng agent hiệu quả

Chúng tôi đã làm việc với hàng chục team xây dựng LLM agents...

![Sơ đồ augmented LLM](assets/img_01.png)
```

## Lệnh curl mẫu

```bash
# Tạo folder
mkdir -p output/building-effective-agents/assets

# Tải ảnh
curl -L -o output/building-effective-agents/assets/img_01.png "https://example.com/image.png"
```
