# MCP và kiến trúc agent: Từ tools đến AI team

**Tác giả:** Research Team  
**Ngày:** 14 tháng 3, 2026  
**Thể loại:** AI · MCP · Architecture

---

## Tóm tắt

Bài viết tổng hợp hai chủ đề liên quan trực tiếp đến cách xây AI agents hiện đại: **MCP** (Model Context Protocol) và **skill-based agents**. Nội dung giải thích vì sao LLM quyết định tool dựa trên context + danh sách tools + schema, vì sao quá nhiều tools làm agent kém thông minh, kiến trúc chuyển từ "1 agent + 500 tools" sang "AI team", và hướng tiến hóa tiếp theo: skill systems, capability platform, memory-centric agents.

---

## 1. MCP: Ý nghĩa cốt lõi

**Model Context Protocol (MCP)** có ý nghĩa quan trọng nhất ở một ý rất cốt lõi:

> MCP tách phần "kết nối tới dịch vụ bên ngoài" ra khỏi application của bạn và chuẩn hóa nó thành các server riêng.

Nói ngắn gọn: **MCP giúp bạn không phải tự viết integration code cho mọi API.**

### Vấn đề lớn khi build AI app (trước MCP)

Giả sử user hỏi: *"Có bao nhiêu pull request đang mở trên GitHub của tôi?"*

Để trả lời, bạn phải: gọi GitHub API, lấy repo list, lấy pull request, parse data, tạo tool schema cho LLM, viết function gọi API, maintain code.

Nếu muốn hỗ trợ GitHub, Slack, Google Drive, Jira, Notion, Database — bạn phải viết hàng trăm integration tools. Đây chính là pain lớn của AI agent systems.

### MCP giải quyết bằng cách nào

Thay vì mỗi app viết integration riêng, hãy tạo **MCP servers**.

```
Claude
   │
MCP Client (app của bạn)
   │
GitHub MCP Server
   │
GitHub API
```

GitHub MCP server đã có sẵn: `get_repos()`, `get_pull_requests()`, `get_issues()`, `create_pr()`. App của bạn chỉ cần connect vào MCP server — không cần viết toàn bộ integration.


### Hệ sinh thái plugin cho AI

MCP tạo ra "plugin ecosystem cho AI":

| Hệ sinh thái | Plugin |
|--------------|--------|
| Browser | Extension |
| VSCode | Extension |
| WordPress | Plugin |
| AI system | MCP servers |

AI có thể dùng tool của người khác mà không cần implement lại. MCP đang cố gắng trở thành **"USB-C của AI tools"** — nếu mọi service đều cung cấp MCP server, Claude, Cursor, Agents, Copilot, OpenAI đều có thể dùng chung tool.

### MCP clients

**MCP client** là thành phần kết nối ứng dụng (Claude, Cursor, agent platform) với MCP servers. Client gửi `ListToolsRequest`, nhận danh sách tools, chuyển cho LLM; khi LLM sinh tool call, client gửi `CallToolRequest` tới server tương ứng và trả kết quả về. MCP client thường được tích hợp sẵn trong Claude Desktop, Cursor, hoặc các agent framework — developer chỉ cần cấu hình kết nối tới MCP servers, không cần implement protocol từ đầu.

---

## 2. LLM quyết định tool thế nào

LLM quyết định gọi tool dựa trên **ba thứ chính**:

1. **Context** (prompt / conversation) — toàn bộ ngữ cảnh: câu hỏi user, lịch sử hội thoại, system prompt
2. **Danh sách tools** — server cung cấp danh sách tools; danh sách này chính là *capabilities* của agent
3. **Schema + description** của từng tool — tên, mô tả, parameters; LLM không hiểu API, chỉ hiểu metadata này

Công thức đơn giản:

```
Tool choice = f(
  user prompt,
  conversation history,
  available tools,
  tool descriptions,
  tool schemas
)
```

### Luồng hoạt động thực tế

1. Client gửi `ListToolsRequest` → Server trả `ListToolsResult` (danh sách tools)
2. Server gửi cho LLM: User question + list tools + tool schema
3. LLM suy luận: question → cần tool nào → sinh `tool_call`
4. Server gọi MCP: `CallToolRequest` → MCP server thực thi → trả `CallToolResult`
5. Server gửi result lại cho LLM → LLM tạo câu trả lời

**LLM không trực tiếp gọi API.** LLM chỉ đọc câu hỏi, xem danh sách tools, quyết định tool phù hợp, sinh ra tool call. MCP chuẩn hóa cách cung cấp và gọi tool.

### Vai trò của schema

Tool schema chính là **interface giữa LLM và code**. Nếu schema không rõ, LLM sẽ gọi sai. Trong hệ thống agent hiện đại: **tools = capability**, **prompt = reasoning context**, **schema = interface**. LLM giống planner; tools giống workers.

---

## 3. Vấn đề context: Tools chiếm token

Một phê bình phổ biến về tool-use và MCP: **danh sách tools + schema thực sự được đưa vào context của LLM** — tiêu tốn token trong context window.

### Vì sao tools chiếm context

Payload gửi LLM thường gồm: messages (system, history, user) + tools (name, description, schema). Mỗi tool có thể tốn 100–500 tokens. Nếu có 100 tools: `100 × 200 ≈ 20k tokens` — chỉ riêng danh sách tool đã chiếm 20k context.

### Vì sao trở thành vấn đề

LLM có context window hữu hạn. Nếu tools chiếm nhiều token thì prompt thực sự của user bị giảm không gian reasoning → model reasoning kém hơn, chi phí token tăng, latency tăng.

Một agent production có thể có 200, 500, thậm chí 1000 tools. Gửi tất cả vào context giống như bắt một kỹ sư đọc 500 trang manual trước khi trả lời câu hỏi đơn giản.

### Giải pháp: Tool routing / tool retrieval

Các hệ thống agent hiện đại **không** gửi toàn bộ tools. Họ dùng **tool routing** hoặc **tool retrieval** — ý tưởng giống RAG nhưng cho tools:

```
User query
   ↓
Tool retrieval
   ↓
Relevant tools (5–10)
   ↓
LLM
```

MCP không ép bạn gửi toàn bộ tools. Bạn có thể: List tools → Filter → Send subset to LLM.

**Quy luật:** càng nhiều tools → agent càng kém thông minh. Các system tốt thường giới hạn 10–30 tools cho mỗi agent.

---

## 4. Skill-based agents: Từ tool list lớn sang AI team

Sau khi triển khai MCP hoặc tool-use ở quy mô lớn, nhiều người nhận ra: **Agent có quá nhiều tools thường hoạt động kém hơn.**

Hệ thống hiện đại chuyển từ:

```
1 agent + rất nhiều tools
```

sang:

```
nhiều agent nhỏ + mỗi agent có ít tools
```

Đây chính là **skill-based agents** hoặc **AI team architecture**.

### Vấn đề của tool list lớn

Với 300 tools (GitHub, Slack, Notion, DB, filesystem, browser, calendar, email...), LLM phải read → hiểu → so sánh giữa 300 lựa chọn. Đây là **decision explosion**. Model thường: chọn sai tool, không gọi tool, gọi tool quá nhiều.

### Nguyên lý cognitive load

LLM giống con người: **quá nhiều lựa chọn → quyết định kém hơn**. Nếu model chỉ thấy 5 tools, decision rất rõ. Nếu thấy 500 tools, decision space trở nên nhiễu.

### Kiến trúc mới: AI team

Thay vì một agent có 500 tools:

```
Coordinator agent
   │
   ├─ GitHub agent
   ├─ Slack agent
   ├─ Database agent
   ├─ Browser agent
   └─ Filesystem agent
```

Mỗi agent chỉ có 5–20 tools. LLM reasoning tốt hơn nhiều.

Ví dụ: User hỏi *"What repositories do I have?"* → Coordinator suy luận: question → GitHub domain → gọi `github-agent`. GitHub agent chỉ có `get_repos`, `get_pull_requests`, `get_issues`, `create_pr` — decision rất dễ.

### MCP trong kiến trúc này

MCP trở thành tool infrastructure:

```
Coordinator Agent
      │
GitHub Agent  → GitHub MCP
Slack Agent   → Slack MCP
DB Agent      → Database MCP
```

Trong agent architecture mới: **tools = capabilities**, **agents = skill groups**. Thay vì 1 agent với 500 capabilities, ta có 10 agents, mỗi agent 10 capabilities.

Kiến trúc này rất giống tổ chức con người: một công ty không có 1 người biết 500 kỹ năng mà có nhiều người, mỗi người một chuyên môn.

### Skill vs Tool

Khác biệt quan trọng: **Tool** là 1 function (ví dụ `get_repos()`); **Skill** là 1 workflow gồm nhiều bước. Ví dụ skill `analyze_repository_health` có thể gồm: search repos → get pull requests → analyze commits → generate summary. Tức là **skill = orchestrated tools**. Agent không còn thấy 200 tools nữa — nó thấy 10 skills.

Cấu trúc phân tầng:

```
Agent
   ├── Workflow A
   │       ├── Skill 1
   │       └── Skill 2
   │
   ├── Workflow B
   │       ├── Skill 3
   │       └── Skill 4
   │
   ▼
Capabilities
   ├ web search
   ├ database query
   ├ file read
   └ code execution
```

Agent chọn workflow → workflow gồm các skill → mỗi skill gọi capabilities (tools) bên dưới.

Ví dụ cụ thể:

| Tầng | Ví dụ |
|------|-------|
| **Agent** | CodingAgent |
| **Workflow** | fix_bug_workflow, write_feature_workflow, review_pr_workflow |
| **Skill** | search_codebase, write_patch, run_tests, summarize_changes |
| **Capabilities** | read_file, execute_python, git_commit, terminal |

---

## 5. Tiến hóa kiến trúc agent

Nhìn vào lịch sử ngắn của LLM → tool use → agent → multi-agent, có thể thấy hướng tiến hóa khá rõ. Nhiều công ty (OpenAI, Anthropic, Cursor, LangChain) đang nói tới các bước sau.

### Giai đoạn 1: Tool-based agents (hiện tại)

Mô hình cơ bản: LLM → Tool selection → Tool execution. Các thành phần: prompt, tools, tool schema, execution layer. Đây là agent thế hệ 1. Vấn đề: quá nhiều tools, reasoning yếu khi tool list lớn, khó scale.

### Giai đoạn 2: Multi-agent / AI team (đang dùng)

Thay vì 1 agent + 200 tools, có Coordinator → Specialized agents. Mỗi agent: ít tools, domain rõ ràng, prompt riêng. Ưu điểm: reasoning tốt hơn, dễ scale, giống tổ chức con người.

### Giai đoạn 3: Skill-based systems (đang hình thành)

Chuyển từ tools sang skills. Tool = 1 function; Skill = 1 workflow (orchestrated tools). Agent thấy 10 skills thay vì 200 tools.

### Giai đoạn 4: AI capability platform

Thay vì agent → tools, có **AI capability layer**:

```
LLM
 ↓
Capability registry
 ↓
Skills
 ↓
Tools
 ↓
APIs
```

Tức là dạng "Operating System cho AI" — capability registry, skill marketplace, agent orchestration, memory layer, tool infrastructure (MCP).

### Giai đoạn 5: Memory-centric agents

Agent hiện nay gần như stateless. Tương lai: persistent memory, knowledge graph. Agent không chỉ react mà còn learn, adapt, plan long-term.

### Giai đoạn 6: Autonomous systems

Một số research lab hướng tới: Goal → Planner → Task graph → Agents → Tools. Agent tự chia task, spawn sub-agents, tự sửa lỗi.

### MCP trong tiến hóa này

MCP đóng vai trò **infrastructure layer** — giống USB, HTTP, POSIX: chuẩn giao tiếp. Trong hệ thống lớn: Agent → Skills → MCP tools → Services.

Insight: Agent architecture đang tiến hóa theo hướng giống tổ chức con người — Tools = workers, Skills = departments, Agents = employees, Coordinator = manager.

---

## Kết luận

- **MCP** chuẩn hóa cách LLM truy cập công cụ và dịch vụ bên ngoài — giảm integration code, tạo ecosystem tool cho AI; đóng vai trò infrastructure layer (USB/HTTP của AI tools)
- **LLM quyết định tool** dựa trên context + danh sách tools + schema; tool schema là interface giữa LLM và code
- **Tools chiếm context** — quá nhiều tools làm agent kém thông minh; giải pháp: tool routing, filtering, hierarchical agents
- **Skill-based agents** chuyển từ 1 agent + nhiều tools sang AI team: nhiều agent nhỏ, mỗi agent ít tools — giống tổ chức con người
- **Tiến hóa tiếp theo:** Skill systems → Capability platform → Memory-centric → Autonomous; kiến trúc agent đang tiến tới mô hình giống tổ chức con người

---

## Tài liệu tham khảo

- Anthropic — [Model Context Protocol](https://modelcontextprotocol.io/)
- LangChain, OpenAI Agents, Claude Code — tool routing và capability selection
