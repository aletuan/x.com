# Plan: Cải thiện Layout YouTube Player

## Mục tiêu

Làm rõ ràng, trong sáng, đơn giản và dễ sử dụng. Tập trung vào tính rõ ràng, trong sáng, đơn giản và dễ sử dụng.

---

## Layout đã chọn: Phương án B

```
┌─────────────────────────────────────────────────────────┐
│ Header: Title                          [Theme toggle]    │
├──────────────────────┬──────────────────────────────────┤
│                      │ Transcript (sync)      [VI] [EN]  │
│   Video (55–60%)     │ ┌──────────────────────────────┐ │
│   (16:9)             │ │ Segment trước (mờ)           │ │
│                      │ │ ► Segment hiện (nổi bật)      │ │
│                      │ │ Segment sau (mờ)              │ │
│                      │ └──────────────────────────────┘ │
└──────────────────────┴──────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Tóm tắt                                                 │
│ Overview (3–4 dòng, max-width: 65ch)                    │
│                                                         │
│ Các phần đáng chú ý                                     │
│ • [00:08] ... (click → seek video)                      │
│ • [08:48] ...                                           │
└─────────────────────────────────────────────────────────┘
```

**Lý do:**
- Video + Transcript cạnh nhau = cặp "xem + đọc" rõ ràng
- Summary full width = dễ đọc, line length hợp lý (65–75 ký tự)
- Không dùng sticky video

---

## Danh sách thay đổi

### 1. Layout (generate_player.py)

| # | Thay đổi | Chi tiết |
|---|----------|----------|
| 1.1 | Container max-width | Tăng lên ~960px (hoặc 1024px) để chứa 2 cột |
| 1.2 | Row 1: Video \| Transcript | `display: flex` hoặc `grid`; Video ~55%, Transcript ~45% |
| 1.3 | Row 2: Summary full width | `grid-column: 1 / -1` hoặc block riêng |
| 1.4 | Responsive | `@media (max-width: 767px)`: stack dọc (Video → Transcript → Summary) |

### 2. Transcript

| # | Thay đổi | Chi tiết |
|---|----------|----------|
| 2.1 | Hiển thị 2–3 dòng | Segment trước (opacity 0.6) + hiện tại (nổi bật) + sau (opacity 0.6) |
| 2.2 | Lang toggle | Cập nhật: chip/tab [VI] [EN] rõ hơn, min 44px touch target |
| 2.3 | Phân biệt rõ Transcript | Nền nhẹ khác (var(--bg)), border nhẹ |

### 3. Summary

| # | Thay đổi | Chi tiết |
|---|----------|----------|
| 3.1 | Overview line length | `max-width: 65ch` cho phần text dài |
| 3.2 | Highlights clickable | Parse `[MM:SS]` → click seek video tới thời điểm đó |
| 3.3 | Phân cấp | H3 "Các phần đáng chú ý" rõ ràng, spacing hợp lý |

### 4. Icons & Accessibility

| # | Thay đổi | Chi tiết |
|---|----------|----------|
| 4.1 | Theme toggle | Thay emoji ☀/🌙 bằng SVG (sun/moon) |
| 4.2 | aria-label | Đảm bảo tất cả icon-only buttons có aria-label |

### 5. JavaScript

| # | Thay đổi | Chi tiết |
|---|----------|----------|
| 5.1 | updateTranscript | Trả về 3 segments (prev, current, next) thay vì 1 |
| 5.2 | Highlight click → seek | Parse timestamp từ highlight text, gọi `player.seekTo(seconds)` |
| 5.3 | Render 3 dòng | DOM: 3 div/span cho prev/current/next |

---

## Thứ tự triển khai

1. **Layout cơ bản** — CSS grid/flex cho Video | Transcript, Summary full width
2. **Responsive** — Mobile stack dọc
3. **Transcript 2–3 dòng** — Logic JS + DOM
4. **Highlights clickable** — Parse [MM:SS], seekTo
5. **Theme toggle SVG** — Thay emoji
6. **Polish** — Spacing, typography, contrast

---

## File cần sửa

- `skills/youtube-crawl-translate/scripts/generate_player.py` — toàn bộ HTML/CSS/JS trong `build_html()`

---

## Không làm

- Không dùng sticky video
- Không thêm animation phức tạp (trừ transition cơ bản)
- Không thay đổi logic fetch transcript, sync offset, v.v.
