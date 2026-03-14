# Output — Kết quả crawl, dịch, tóm tắt

Thư mục chứa output từ các pipeline: YouTube crawl-translate (player + transcript EN/VI), bài viết dịch (article.md).

## Cấu trúc

### Bài viết (article)

| # | Thư mục | Nội dung |
|---|---------|----------|
| 1 | [building-effective-agents](./building-effective-agents/article.md) | Xây dựng agent hiệu quả (Anthropic) |
| 2 | [code-execution-with-mcp](./code-execution-with-mcp/article.md) | Thực thi code với MCP (Anthropic) |

### YouTube (player + transcript EN/VI)

| # | Thư mục | Mô tả |
|---|---------|-------|
| 1 | [a-day-in-my-life-lex-fridman-0m3hGZvD-0s](./a-day-in-my-life-lex-fridman-0m3hGZvD-0s/) | A day in my life \| Lex Fridman |
| 2 | [agent-skills-or-mcp-in-the-era-of-claude-code-pvxNcQTcIy4](./agent-skills-or-mcp-in-the-era-of-claude-code-pvxNcQTcIy4/) | Agent skills or MCP in the era of Claude Code |
| 3 | [andrej-karpathy-software-is-changing-again-LCEmiRjPEtQ](./andrej-karpathy-software-is-changing-again-LCEmiRjPEtQ/) | Andrej Karpathy: Software is changing again |
| 4 | [day-in-the-life-of-andrej-karpathy-lex-fridman-podcast-clips-iu3LJY8N_9s](./day-in-the-life-of-andrej-karpathy-lex-fridman-podcast-clips-iu3LJY8N_9s/) | Day in the life of Andrej Karpathy (Lex Fridman clips) |
| 5 | [dont-build-agents-build-skills-instead-barry-zhang-mahesh-mu-CEvIs9y1uog](./dont-build-agents-build-skills-instead-barry-zhang-mahesh-mu-CEvIs9y1uog/) | Don't build agents, build skills instead |
| 6 | [from-writing-code-to-managing-agents-most-engineers-arent-re-wEsjK3Smovw](./from-writing-code-to-managing-agents-most-engineers-arent-re-wEsjK3Smovw/) | From writing code to managing agents |
| 7 | [how-to-code-with-ai-agents-advice-from-openclaw-creator-pete-wKy1_KLcxcs](./how-to-code-with-ai-agents-advice-from-openclaw-creator-pete-wKy1_KLcxcs/) | How to code with AI agents (OpenClaw creator) |
| 8 | [how-to-learn-and-master-a-new-skill-_ySbzVXiwzQ](./how-to-learn-and-master-a-new-skill-_ySbzVXiwzQ/) | How to learn and master a new skill |
| 9 | [prompt-engineering-is-dead-Cs7QiSi8KLY](./prompt-engineering-is-dead-Cs7QiSi8KLY/) | Prompt engineering is dead |
| 10 | [should-you-learn-coding-now-anthropic-ceo-explains-EdZWPB1fIJc](./should-you-learn-coding-now-anthropic-ceo-explains-EdZWPB1fIJc/) | Should you learn coding now? (Anthropic CEO) |
| 11 | [vertical-ai-agents-could-be-10x-bigger-than-saas-ASABxNenD_U](./vertical-ai-agents-could-be-10x-bigger-than-saas-ASABxNenD_U/) | Vertical AI agents could be 10x bigger than SaaS |
| 12 | [why-mcp-really-is-a-big-deal-model-context-protocol-with-tim-FLpS7OfD5-s](./why-mcp-really-is-a-big-deal-model-context-protocol-with-tim-FLpS7OfD5-s/) | Why MCP really is a big deal (Model Context Protocol with Tim) |

### Khác (chưa đầy đủ transcript/dịch)

| Thư mục | Ghi chú |
|---------|---------|
| [atlassian-ceo-on-the-saas-apocalypse-ai-agents-what-comes-ne-0lzo2tFBFy8](./atlassian-ceo-on-the-saas-apocalypse-ai-agents-what-comes-ne-0lzo2tFBFy8/) | Chỉ có player |
| [inside-claude-code-with-its-creator-boris-cherny-PQU9o_5rHC4](./inside-claude-code-with-its-creator-boris-cherny-PQU9o_5rHC4/) | Chỉ có player |
| [test-video](./test-video/) | Test |

## Xem player

```bash
cd output/<thư-mục> && python -m http.server 8765
```

Mở http://localhost:8765/player.html

## Nguồn pipeline

- **YouTube crawl-translate:** `skills/youtube-crawl-translate/` — Apify transcript, Claude dịch VI
- **Article:** Dịch bài từ Anthropic Engineering, lưu article.md + assets
