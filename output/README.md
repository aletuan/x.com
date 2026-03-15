# Output — Kết quả crawl, dịch, tóm tắt

Thư mục chứa output từ các pipeline: YouTube crawl-translate (player + transcript EN/VI), bài viết dịch (article.md).

## Cấu trúc

### Bài viết (article)

| # | Thư mục | Nội dung |
|---|---------|----------|
| 1 | [building-effective-agents](./building-effective-agents/article.md) | Xây dựng agent hiệu quả (Anthropic) |
| 2 | [code-execution-with-mcp](./code-execution-with-mcp/article.md) | Thực thi code với MCP (Anthropic) |

### Blog (nghiên cứu AI agents)

| # | Bài viết | Mô tả |
|---|----------|-------|
| 1 | [AI đòn bẩy cho PMs](../blog/01-ai-leverage-for-pms/article.md) | Cách PM dùng sub-agents như leverage thực sự |
| 2 | [Self-improving skills](../blog/02-self-improving-skills/article.md) | Kỹ năng tự cải thiện và skill graph |
| 3 | [Kỷ nguyên agent programming](../blog/03-agent-programming-paradigm/article.md) | Khi đơn vị lập trình là agent, không còn file |
| 4 | [MCP và kiến trúc agent](../blog/04-mcp-agent-architecture/article.md) | MCP, skill-based agents, tool routing |

### YouTube (player + transcript EN/VI)

| # | Video |
|---|-------|
| 1 | [A day in my life \| Lex Fridman](http://localhost:8765/player.html?dir=output/a-day-in-my-life-lex-fridman-0m3hGZvD-0s) |
| 2 | [Agent skills or MCP in the era of Claude Code](http://localhost:8765/player.html?dir=output/agent-skills-or-mcp-in-the-era-of-claude-code-pvxNcQTcIy4) |
| 3 | [Andrej Karpathy: Software is changing again](http://localhost:8765/player.html?dir=output/andrej-karpathy-software-is-changing-again-LCEmiRjPEtQ) |
| 4 | [Day in the life of Andrej Karpathy (Lex Fridman clips)](http://localhost:8765/player.html?dir=output/day-in-the-life-of-andrej-karpathy-lex-fridman-podcast-clips-iu3LJY8N_9s) |
| 5 | [Don't build agents, build skills instead](http://localhost:8765/player.html?dir=output/dont-build-agents-build-skills-instead-barry-zhang-mahesh-mu-CEvIs9y1uog) |
| 6 | [From writing code to managing agents](http://localhost:8765/player.html?dir=output/from-writing-code-to-managing-agents-most-engineers-arent-re-wEsjK3Smovw) |
| 7 | [How to code with AI agents (OpenClaw creator)](http://localhost:8765/player.html?dir=output/how-to-code-with-ai-agents-advice-from-openclaw-creator-pete-wKy1_KLcxcs) |
| 8 | [How to learn and master a new skill](http://localhost:8765/player.html?dir=output/how-to-learn-and-master-a-new-skill-_ySbzVXiwzQ) |
| 9 | [Prompt engineering is dead](http://localhost:8765/player.html?dir=output/prompt-engineering-is-dead-Cs7QiSi8KLY) |
| 10 | [Should you learn coding now? (Anthropic CEO)](http://localhost:8765/player.html?dir=output/should-you-learn-coding-now-anthropic-ceo-explains-EdZWPB1fIJc) |
| 11 | [Vertical AI agents could be 10x bigger than SaaS](http://localhost:8765/player.html?dir=output/vertical-ai-agents-could-be-10x-bigger-than-saas-ASABxNenD_U) |
| 12 | [Why MCP really is a big deal (Model Context Protocol with Tim)](http://localhost:8765/player.html?dir=output/why-mcp-really-is-a-big-deal-model-context-protocol-with-tim-FLpS7OfD5-s) |
| 13 | [Atlassian CEO on the SaaS Apocalypse, AI Agents & What Comes Next](http://localhost:8765/player.html?dir=output/atlassian-ceo-on-the-saas-apocalypse-ai-agents-what-comes-ne-0lzo2tFBFy8) |
| 14 | [Inside Claude Code With Its Creator Boris Cherny](http://localhost:8765/player.html?dir=output/inside-claude-code-with-its-creator-boris-cherny-PQU9o_5rHC4) |
| 15 | [LMFAO - Party Rock Anthem ft. Lauren Bennett, GoonRock](http://localhost:8765/player.html?dir=output/test-video) |
| 16 | [Beyond Vibe Coding with Addy Osmani](http://localhost:8765/player.html?dir=output/beyond-vibe-coding-with-addy-osmani-dHIppEqwi0g) |

### Khác (chưa có transcript_vi)

| Thư mục | Ghi chú |
|---------|---------|
| [atlassian-ceo-on-the-saas-apocalypse-ai-agents-what-comes-ne-0lzo2tFBFy8](./atlassian-ceo-on-the-saas-apocalypse-ai-agents-what-comes-ne-0lzo2tFBFy8/) | Chưa dịch VI |
| [inside-claude-code-with-its-creator-boris-cherny-PQU9o_5rHC4](./inside-claude-code-with-its-creator-boris-cherny-PQU9o_5rHC4/) | Chưa dịch VI |
| [test-video](./test-video/) | Test |

## Xem player

Chạy HTTP server từ **project root**:

```bash
cd /path/to/X.com && python -m http.server 8765
```

Mở: `http://localhost:8765/player.html?dir=output/<thư-mục>`

Ví dụ: http://localhost:8765/player.html?dir=output/how-to-learn-and-master-a-new-skill-_ySbzVXiwzQ

## Nguồn pipeline

- **YouTube crawl-translate:** `skills/youtube-crawl-translate/` — Apify transcript, Claude dịch VI
- **Article:** Dịch bài từ Anthropic Engineering, lưu article.md + assets

## Đồng bộ output thiếu tóm tắt/timeline

Chạy script để summarize + translate các folder YouTube thiếu thông tin:

```bash
python scripts/sync_youtube_outputs.py --skip-test
```
