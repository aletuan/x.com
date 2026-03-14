# Self-Improving Skills: Khi skill tự tiến hóa theo thời gian

**Tác giả:** Research Team  
**Ngày:** 13 tháng 3, 2026  
**Thể loại:** AI · Agents · System Design

---

## Tóm tắt

Kỹ năng thường là tĩnh, nhưng môi trường luôn thay đổi. Bài viết phân tích vấn đề skill degradation, kiến trúc self-improving skills của Cognee, và lý do tương lai của AI agents không phải "prompt library" mà là "skill graph".

---

## Vấn đề cốt lõi

> *Skills cannot stay static while systems around them constantly change.*

Mô hình SKILL.md đang trở thành chuẩn phổ biến (Claude Code, Cursor, Cognee). Nhưng vấn đề vẫn chưa được giải quyết:

**Một skill hoạt động tốt vài tuần trước có thể âm thầm thất bại khi:**

- Codebase thay đổi
- Model thay đổi hành vi
- Loại nhiệm vụ người dùng yêu cầu thay đổi

Trong nhiều hệ thống, lỗi này không được phát hiện cho đến khi output trở nên kém hoặc hệ thống bắt đầu fail hoàn toàn.

---

## Ba nguồn degradation chính

| Nguồn | Ví dụ |
|-------|-------|
| **Model drift** | Prompt viết 2 tháng trước → Model update → Output quality giảm |
| **Codebase change** | Tool `search_code` giả định file structure cũ → Codebase đổi → Skill fail |
| **Task distribution change** | Trước: "summarize doc" → Sau: "compare docs" → Skill cũ không phù hợp |

---

## Ý tưởng: Skills như thành phần sống

Để thư mục skills thực sự hữu ích, ta phải coi chúng như **các thành phần sống của hệ thống**, không phải file prompt cố định.

Đây là hướng của **cognee-skills**: không chỉ lưu và routing skills tốt hơn, mà còn giúp skills **tự cải thiện** khi chúng hoạt động kém hoặc thất bại.

---

## Kiến trúc: Add → Cognify → Search → Observe → Promote

Cognee tổ chức skills qua pipeline add-cognify-search:

### 1. Add (Ingest)

Parser đọc mỗi SKILL.md, trích xuất frontmatter và instructions, scan bundled resources. Mỗi skill có:

- Stable identity
- Metadata
- Content hashes (để phát hiện thay đổi)

### 2. Cognify (Enrich)

LLM extraction tạo ra:

- **Task patterns** mà skill có thể giải quyết
- Complexity level
- Tags
- Trigger phrases
- Instruction summary
- Description đã làm sạch

Task patterns trở thành các node riêng trong graph. Skills được kết nối với chúng qua quan hệ "solves".

**Chuyển đổi quan trọng:** Không còn lưu "documents về skills". Đang **xây knowledge graph** của skills, intents và relationships.

### 3. Search (Route)

Routing không chỉ là keyword match. Retrieval layer làm ba việc:

- Graph lookup của learned preferred edges từ past runs
- Semantic search trên task-pattern descriptions
- Semantic search trên skill summaries

Ranking cuối cùng **kết hợp semantic similarity với historical success**.

Câu hỏi tốt hơn: không phải "skill nào giống prompt này?" mà "skill nào thường hoạt động cho loại task này?"

### 4. Observe & Promote (Learn)

Sau mỗi lần chạy skill, hệ thống ghi lại:

- Task đã thực hiện
- Skill được chọn
- Thành công hay thất bại
- Lỗi, feedback người dùng

Runs đầu tiên vào short-term memory (Redis). **Promote()** chuyển runs quan trọng vào long-term graph và cập nhật preference weights giữa task patterns và skills.

**Cả success và failure đều có giá trị:** Success dạy router tin gì hơn; failure dạy tránh gì lần sau.

---

## Chu trình Self-Improvement

```
run skill
   ↓
log result (observe)
   ↓
detect failure
   ↓
analyze cause (inspect)
   ↓
modify prompt (amend)
   ↓
evaluate
   ↓
deploy new skill (nếu tốt hơn) / rollback (nếu không)
```

---

## Bốn giai đoạn evolution của AI software

1. **Prompt** — Chỉ prompt
2. **Tools + Prompt** — Thêm tools
3. **Agents + Skills** — Agents với skill library
4. **Self-improving Agents** — Skills học từ failure và feedback

---

## Prompt engineering vs. Skills system

| Prompt Engineering | Skills System |
|--------------------|---------------|
| Software tĩnh | Software có thể tiến hóa |
| Viết xong, dùng mãi | Observe → Inspect → Amend → Evaluate |
| Không học từ failure | Failure = data để phân tích |

---

## Implementations thực tế

- **LangGraph:** Reflection nodes, evaluation nodes, memory
- **Devin-style systems:** Task history, error traces, self-correction
- **Claude Code / Cursor:** Skills folder, skill routing, skill updates
- **Cognee:** Graph skills, observe-promote loop, feedback-driven routing

---

## Kết luận

- Skills không thể đứng yên trong khi hệ thống xung quanh thay đổi
- Self-improving skills = ingest → route → execute → observe → promote → route tốt hơn
- Tương lai của AI agents không phải "prompt library" mà là **skill graph**
- Engineer giỏi xây **learning system**, không chỉ viết prompt tốt hơn

---

## Tài liệu tham khảo

- Cognee, [Structure Your Skills with Cognee](https://www.cognee.ai/blog/tutorials/structure-your-skills-with-cognee)
- Cognee, [Building Self-Improving Skills for Agents](https://www.cognee.ai/blog/deep-dives/building-self-improving-skills-for-agents)
- Cognee, [AI Memory Auto-Optimization: User Feedback Improves Search](https://www.cognee.ai/blog/cognee-news/product-announcement-auto-optimization)
