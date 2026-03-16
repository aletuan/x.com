#!/usr/bin/env python3
"""
Generate YouTube player HTML with transcript sync, dark mode, agentic UI.
Uses shared player template + metadata.json to avoid duplicating HTML per video.
Player loads metadata.json and transcript at runtime.
Usage: python generate_player.py <video_id> <video_title> <transcript_json> <summary> <output_dir>
Or: pass args via stdin as JSON object: {video_id, video_title, transcript, summary, output_dir}
"""
import json
import html
import re
import subprocess
import sys
from pathlib import Path


def escape_js(s):
    """Escape string for use in JavaScript."""
    return json.dumps(s, ensure_ascii=False)


def _format_duration(seconds: int) -> str:
    """Format seconds to 'X phút' or 'X phút Y giây'."""
    if not seconds:
        return "—"
    mins = seconds // 60
    secs = seconds % 60
    if secs == 0:
        return f"{mins} phút"
    return f"{mins} phút {secs} giây"


def _format_duration_short(seconds: int) -> str:
    """Format seconds to 'X phút' for stat box."""
    if not seconds:
        return "—"
    mins = (seconds + 29) // 60
    return f"{mins} phút"


def _format_published_at(iso_str: str | None) -> str:
    """Format ISO date to 'DD Month YYYY'."""
    if not iso_str:
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        months = ["tháng 1", "tháng 2", "tháng 3", "tháng 4", "tháng 5", "tháng 6",
                  "tháng 7", "tháng 8", "tháng 9", "tháng 10", "tháng 11", "tháng 12"]
        return f"{dt.day} {months[dt.month - 1]}, {dt.year}"
    except Exception:
        return iso_str


def build_html(
    video_id: str,
    video_title: str,
    transcript: list,
    summary: str = "",
    summary_overview: str = "",
    summary_overview_vi: str = "",
    summary_highlights: list | str = "",
    channel_title: str = "",
    published_at: str = "",
    duration_seconds: int | None = None,
) -> str:
    """Build full HTML document (legacy - embeds data). Kept for backward compat."""
    transcript_js = json.dumps(transcript, ensure_ascii=False)
    title_esc = html.escape(video_title)
    overview = summary_overview or summary
    overview_vi = summary_overview_vi or ""
    overview_esc = html.escape(overview).replace("\n", "<br>") if overview else ""
    overview_vi_esc = html.escape(overview_vi).replace("\n", "<br>") if overview_vi else ""
    if isinstance(summary_highlights, list):
        highlights = summary_highlights
    elif isinstance(summary_highlights, str) and summary_highlights.strip():
        highlights = [s.strip() for s in summary_highlights.strip().split("\n") if s.strip()]
    else:
        highlights = []
    def make_highlight_li(h):
        """Parse [MM:SS] from highlight text and wrap in clickable span."""
        m = re.search(r'\[(\d{1,2}):(\d{2})\]', h)
        if m:
            mins, secs = int(m.group(1)), int(m.group(2))
            ts_sec = mins * 60 + secs
            before = h[:m.start()]
            ts_str = m.group(0)
            after = h[m.end():]
            return f'<li><span class="highlight-ts" data-seek="{ts_sec}" role="button" tabindex="0">{html.escape(before)}<strong>{html.escape(ts_str)}</strong>{html.escape(after)}</span></li>'
        return f'<li>{html.escape(h)}</li>'

    highlights_html = "".join(make_highlight_li(h) for h in highlights) if highlights else ""

    # Stats
    dur_sec = duration_seconds
    if dur_sec is None and transcript:
        last = transcript[-1]
        dur_sec = int(last["start"] + last["duration"])
    dur_display = _format_duration_short(dur_sec or 0)
    sub_lines = len(transcript)
    num_events = len(highlights)
    published_fmt = _format_published_at(published_at) if published_at else ""
    channel_esc = html.escape(channel_title) if channel_title else ""
    meta_parts = []
    if channel_esc:
        meta_parts.append(f"<span>{channel_esc}</span>")
    if published_fmt:
        meta_parts.append(f"<span> · {published_fmt}</span>")
    video_meta_html = " ".join(meta_parts)

    return f'''<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_esc}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #1a1a1a;
      --surface: #252525;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #ff0000;
      --accent-hover: #cc0000;
      --border: #333;
      --highlight: #2a2a2a;
    }}

    [data-theme="light"] {{
      --bg: #f8fafc;
      --surface: #ffffff;
      --text: #1e293b;
      --text-muted: #64748b;
      --accent: #cc0000;
      --accent-hover: #990000;
      --border: #e2e8f0;
      --highlight: #fef2f2;
    }}

    @media (prefers-reduced-motion: reduce) {{
      * {{ transition: none !important; }}
    }}

    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 0 2rem;
      font-family: 'Inter', system-ui, sans-serif;
      font-size: 16px;
      line-height: 1.6;
      color: var(--text);
      background: var(--bg);
      min-height: 100vh;
    }}

    .container {{ max-width: 1280px; margin: 0 auto; padding: 1.5rem 0; }}

    @media (min-width: 1600px) {{
      .container {{ max-width: 1440px; }}
    }}

    .header-row {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 1rem;
    }}

    .header-brand {{
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }}

    .header-top {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}

    .logo {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--accent);
      font-weight: 700;
      font-size: 1.25rem;
    }}

    .logo svg {{ width: 28px; height: 28px; flex-shrink: 0; }}

    .badge {{
      background: var(--accent);
      color: #fff;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
    }}

    .header-title {{
      font-size: 0.875rem;
      font-weight: 400;
      color: var(--text-muted);
      margin: 0;
      line-height: 1.4;
    }}

    .stats-row {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
      margin-bottom: 1.5rem;
    }}

    @media (max-width: 600px) {{
      .stats-row {{ grid-template-columns: 1fr; }}
    }}

    .stat-box {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
    }}

    .stat-label {{ font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.25rem; }}
    .stat-value {{ font-size: 1.25rem; font-weight: 600; }}

    .watch-row {{
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      margin-bottom: 1.5rem;
    }}

    @media (max-width: 767px) {{
      body {{ padding: 0 1rem; }}
    }}

    .video-wrap {{
      position: relative;
      width: 100%;
      padding-bottom: 56.25%;
      height: 0;
      overflow: hidden;
      border-radius: 12px;
      background: #000;
    }}

    #player {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
    }}

    #player iframe {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
    }}

    .video-meta {{
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 0.5rem;
    }}

    .video-meta a {{ color: var(--accent); text-decoration: none; }}
    .video-meta a:hover {{ text-decoration: underline; }}

    .theme-toggle {{
      flex-shrink: 0;
      width: 44px;
      height: 44px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s, border-color 0.2s;
    }}

    .theme-toggle svg {{ width: 20px; height: 20px; }}
    .theme-toggle .icon-moon {{ display: none; }}
    .theme-toggle .icon-sun {{ display: block; }}
    [data-theme="light"] .theme-toggle .icon-sun {{ display: none; }}
    [data-theme="light"] .theme-toggle .icon-moon {{ display: block; }}
    .theme-toggle:hover {{ background: var(--highlight); }}
    .theme-toggle:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}

    .file-notice {{
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      padding: 1rem;
      background: rgba(0,0,0,0.85);
      color: #fff;
      font-size: 0.85rem;
      text-align: center;
    }}

    .file-notice code {{
      background: rgba(255,255,255,0.2);
      padding: 0.2em 0.4em;
      border-radius: 4px;
    }}

    .transcript-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
    }}

    .transcript-card h2 {{
      font-size: 1rem;
      font-weight: 600;
      margin: 0 0 0.75rem 0;
      color: var(--text);
    }}

    .transcript-header {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.75rem;
    }}

    .lang-chip {{
      min-width: 44px;
      min-height: 44px;
      padding: 0.25rem 0.75rem;
      font-size: 0.85rem;
      font-weight: 500;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s, border-color 0.2s;
    }}

    .lang-chip:hover {{
      background: var(--highlight);
    }}

    .lang-chip.active {{
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }}

    .lang-chip:focus-visible {{
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }}

    .transcript-area {{
      flex: 1;
      min-height: 6rem;
      padding: 1rem;
      background: var(--bg);
      border-radius: 8px;
      border: 1px solid var(--border);
    }}

    .sub-toolbar {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1rem;
      flex-wrap: wrap;
    }}

    .sub-search {{
      flex: 1;
      min-width: 200px;
      padding: 0.5rem 0.75rem;
      font-size: 0.9rem;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
    }}

    .sub-search::placeholder {{ color: var(--text-muted); }}

    .sub-lang-group {{
      display: flex;
      gap: 0.25rem;
    }}

    .sub-lang-btn {{
      padding: 0.4rem 0.75rem;
      font-size: 0.85rem;
      font-weight: 500;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text-muted);
      cursor: pointer;
    }}

    .sub-lang-btn:hover {{ color: var(--text); }}
    .sub-lang-btn.active {{
      background: var(--highlight);
      color: var(--text);
      border-color: var(--text-muted);
    }}

    .transcript-list {{
      max-height: 400px;
      overflow-y: auto;
    }}

    .transcript-item {{
      display: flex;
      gap: 1rem;
      padding: 0.75rem 0;
      border-bottom: 1px solid var(--border);
      cursor: pointer;
      align-items: flex-start;
    }}

    .transcript-item:last-child {{ border-bottom: none; }}
    .transcript-item:hover {{ background: var(--highlight); }}

    .transcript-item.current {{
      background: var(--highlight);
    }}

    .transcript-item.current .transcript-ts {{ color: var(--accent); }}

    .transcript-ts {{
      flex-shrink: 0;
      font-weight: 700;
      font-size: 0.9rem;
      color: var(--text-muted);
      min-width: 3.5rem;
    }}

    .transcript-text {{
      flex: 1;
      min-width: 0;
    }}

    .transcript-text .line-en {{
      font-size: 0.95rem;
      font-weight: 500;
      color: var(--text);
      line-height: 1.5;
    }}

    .transcript-text .line-vi {{
      font-size: 0.9rem;
      font-weight: 400;
      color: var(--text-muted);
      line-height: 1.5;
      margin-top: 0.2rem;
    }}

    .transcript-line {{
      font-size: 0.95rem;
      color: var(--text);
      margin-bottom: 0.35rem;
      line-height: 1.5;
      cursor: pointer;
    }}

    .transcript-line:hover {{ color: var(--accent); }}
    .transcript-line.dim {{ opacity: 0.6; }}
    .transcript-line.current {{
      font-weight: 500;
      color: var(--accent);
      transform: scale(1.02);
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
      background: var(--highlight);
      padding: 0.25rem 0.5rem;
      margin: 0 -0.5rem 0.35rem -0.5rem;
      border-radius: 6px;
    }}

    .tabs {{
      display: flex;
      gap: 0;
      border-bottom: 1px solid var(--border);
      margin-bottom: 1rem;
    }}

    .tab {{
      padding: 0.75rem 1.25rem;
      font-size: 0.9rem;
      font-weight: 500;
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--text-muted);
      cursor: pointer;
      margin-bottom: -1px;
    }}

    .tab:hover {{ color: var(--text); }}
    .tab.active {{
      color: var(--accent);
      border-bottom-color: var(--accent);
    }}

    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}

    .summary-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
    }}

    .summary-card h2 {{
      font-size: 1rem;
      font-weight: 600;
      margin: 0 0 1rem 0;
      color: var(--text);
    }}

    .summary-text {{
      color: var(--text);
      font-size: 0.95rem;
    }}

    .summary-overview {{
      margin-bottom: 1.25rem;
      line-height: 1.6;
      width: 100%;
    }}

    .summary-highlights {{
      margin: 0;
      padding-left: 1.25rem;
    }}

    .summary-highlights li {{
      margin-bottom: 0.5rem;
    }}

    .highlight-ts {{
      cursor: pointer;
      text-decoration: underline;
      text-underline-offset: 2px;
    }}

    .highlight-ts:hover {{
      color: var(--accent);
    }}

    .empty {{
      color: var(--text-muted);
      font-style: italic;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header-row">
      <div class="header-brand">
        <div class="header-top">
          <div class="logo">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
            YouTube Analyzer
          </div>
          <span class="badge">Kết quả</span>
        </div>
        <h1 class="header-title">{title_esc}</h1>
      </div>
      <button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
        <svg class="icon-sun" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        <svg class="icon-moon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      </button>
    </div>

    <div class="stats-row">
      <div class="stat-box"><div class="stat-label">Thời lượng</div><div class="stat-value">{dur_display}</div></div>
      <div class="stat-box"><div class="stat-label">Dòng phụ đề</div><div class="stat-value">{sub_lines}</div></div>
      <div class="stat-box"><div class="stat-label">Sự kiện chính</div><div class="stat-value">{num_events}</div></div>
    </div>

    <div class="watch-row">
      <div>
        <div class="video-wrap">
          <div id="player"></div>
          <div id="fileProtocolNotice" class="file-notice" style="display:none">
            Video không hiển thị khi mở file trực tiếp. Chạy: <code>lsof -ti:8765 | xargs kill -9 2>/dev/null || true; python -m http.server 8765</code> rồi mở <code>http://localhost:8765/player.html</code>
          </div>
        </div>
        <div class="video-meta">
          {video_meta_html}
        </div>
      </div>

      <div class="transcript-card">
        <div class="tabs">
          <button class="tab active" data-tab="summary">Tóm tắt</button>
          <button class="tab" data-tab="timeline">Timeline</button>
          <button class="tab" data-tab="subtitles">Phụ đề</button>
        </div>

        <div id="panel-summary" class="tab-panel active">
          <div class="transcript-header">
            <button class="lang-chip active" id="langVi" aria-label="Tóm tắt tiếng Việt">VI</button>
            <button class="lang-chip" id="langEn" aria-label="Summary in English">EN</button>
          </div>
          <div class="summary-text" id="summaryOverview">
            {f'<div class="summary-overview" id="summaryVi">{overview_vi_esc}</div>' if overview_vi_esc else ''}
            {f'<div class="summary-overview" id="summaryEn">{overview_esc}</div>' if overview_esc else ''}
            {'' if (overview_esc or overview_vi_esc) else '<span class="empty">Chưa có tóm tắt</span>'}
          </div>
        </div>

        <div id="panel-timeline" class="tab-panel">
          <div class="summary-text">
            {f'<ul class="summary-highlights">{highlights_html}</ul>' if highlights_html else '<span class="empty">Chưa có timeline</span>'}
          </div>
        </div>

        <div id="panel-subtitles" class="tab-panel">
          <div class="sub-toolbar">
            <input type="text" class="sub-search" id="subSearch" placeholder="Tìm kiếm trong phụ đề..." aria-label="Tìm kiếm trong phụ đề">
            <div class="sub-lang-group">
              <button class="sub-lang-btn active" id="subLangBilingual" data-mode="bilingual">Song ngữ</button>
              <button class="sub-lang-btn" id="subLangEn" data-mode="en">EN</button>
              <button class="sub-lang-btn" id="subLangVi" data-mode="vi">VI</button>
            </div>
          </div>
          <div class="transcript-area transcript-list" id="transcriptList"></div>
        </div>
      </div>
    </div>

  <script src="https://www.youtube.com/iframe_api"></script>
  <script>
    let transcriptData = {transcript_js};
    let player;
    let pollInterval;

    async function loadTranscriptAtRuntime() {{
      try {{
        const r = await fetch('transcript_vi.json');
        if (r.ok) {{
          const data = await r.json();
          if (Array.isArray(data) && data.length > 0) {{ transcriptData = data; renderTranscriptList(); return; }}
        }}
      }} catch (e) {{}}
      try {{
        const r = await fetch('transcript.json');
        if (r.ok) {{
          const data = await r.json();
          if (Array.isArray(data) && data.length > 0) {{ transcriptData = data; renderTranscriptList(); return; }}
        }}
      }} catch (e) {{}}
    }}
    loadTranscriptAtRuntime();

    function initTheme() {{
      const saved = localStorage.getItem('yt-player-theme');
      document.documentElement.setAttribute('data-theme', saved || 'dark');
    }}

    document.getElementById('themeToggle').addEventListener('click', () => {{
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('yt-player-theme', next);
    }});

    const SYNC_OFFSET = 2;
    function findSegmentIndex(time) {{
      const t = time + SYNC_OFFSET;
      for (let i = 0; i < transcriptData.length; i++) {{
        const s = transcriptData[i];
        if (t >= s.start && t < s.start + s.duration) return i;
      }}
      // Gap: show nearest segment (last passed or next upcoming)
      if (transcriptData.length === 0) return -1;
      for (let i = transcriptData.length - 1; i >= 0; i--) {{
        if (t >= transcriptData[i].start) return i;
      }}
      return 0;
    }}

    const langKey = 'yt-player-lang';
    const subLangKey = 'yt-player-sublang';
    const viEl = document.getElementById('summaryVi');
    const enEl = document.getElementById('summaryEn');
    let showVi = (viEl && enEl) ? (localStorage.getItem(langKey) || 'vi') === 'vi' : !!viEl;
    let subLangMode = localStorage.getItem(subLangKey) || 'bilingual';

    function toggleSummaryLang() {{
      const viEl = document.getElementById('summaryVi');
      const enEl = document.getElementById('summaryEn');
      if (viEl) viEl.style.display = showVi ? 'block' : 'none';
      if (enEl) enEl.style.display = showVi ? 'none' : 'block';
      document.getElementById('langVi')?.classList.toggle('active', showVi);
      document.getElementById('langEn')?.classList.toggle('active', !showVi);
    }}

    document.getElementById('langVi')?.addEventListener('click', () => {{
      showVi = true;
      localStorage.setItem(langKey, 'vi');
      toggleSummaryLang();
    }});
    document.getElementById('langEn')?.addEventListener('click', () => {{
      showVi = false;
      localStorage.setItem(langKey, 'en');
      toggleSummaryLang();
    }});
    toggleSummaryLang();

    document.querySelectorAll('.sub-lang-btn').forEach(btn => {{
      btn.classList.toggle('active', btn.getAttribute('data-mode') === subLangMode);
      btn.addEventListener('click', () => {{
        subLangMode = btn.getAttribute('data-mode');
        document.querySelectorAll('.sub-lang-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        localStorage.setItem(subLangKey, subLangMode);
        renderTranscriptList();
      }});
    }});

    document.getElementById('subSearch')?.addEventListener('input', () => {{
      renderTranscriptList();
    }});

    document.querySelectorAll('.tab').forEach(btn => {{
      btn.addEventListener('click', () => {{
        const tab = btn.getAttribute('data-tab');
        document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('panel-' + tab)?.classList.add('active');
      }});
    }});

    function formatTs(sec) {{
      const m = Math.floor(sec / 60);
      const s = Math.floor(sec % 60);
      return m + ':' + (s < 10 ? '0' : '') + s;
    }}

    function escapeHtml(s) {{
      const div = document.createElement('div');
      div.textContent = s || '';
      return div.innerHTML;
    }}

    function renderTranscriptList() {{
      const list = document.getElementById('transcriptList');
      const searchEl = document.getElementById('subSearch');
      if (!list) return;
      const q = (searchEl?.value || '').trim().toLowerCase();
      const filtered = transcriptData
        .map((seg, i) => ({{ seg, i }}))
        .filter(({{ seg }}) => {{
          if (!q) return true;
          const text = (seg.text || '').toLowerCase();
          const textVi = (seg.textVi || '').toLowerCase();
          return text.includes(q) || textVi.includes(q);
        }});
      list.innerHTML = filtered.map(({{ seg, i }}) => {{
        const start = seg.start ?? 0;
        const text = seg.text || '—';
        const textVi = seg.textVi || '';
        const ts = formatTs(start);
        let content = '';
        if (subLangMode === 'bilingual') {{
          content = `<div class="line-en">${{escapeHtml(text)}}</div>` + (textVi ? `<div class="line-vi">${{escapeHtml(textVi)}}</div>` : '');
        }} else if (subLangMode === 'vi') {{
          content = `<div class="line-en">${{escapeHtml(textVi || text)}}</div>`;
        }} else {{
          content = `<div class="line-en">${{escapeHtml(text)}}</div>`;
        }}
        return `<div class="transcript-item" data-index="${{i}}" data-start="${{start}}" role="button" tabindex="0"><span class="transcript-ts">${{ts}}</span><div class="transcript-text">${{content}}</div></div>`;
      }}).join('');
      list.querySelectorAll('.transcript-item').forEach(el => {{
        el.addEventListener('click', () => {{
          const sec = parseFloat(el.getAttribute('data-start'));
          if (player?.seekTo && !isNaN(sec)) player.seekTo(sec, true);
        }});
        el.addEventListener('keydown', (e) => {{
          if (e.key === 'Enter' || e.key === ' ') {{
            e.preventDefault();
            const sec = parseFloat(el.getAttribute('data-start'));
            if (player?.seekTo && !isNaN(sec)) player.seekTo(sec, true);
          }}
        }});
      }});
      if (player?.getCurrentTime) updateTranscript(player.getCurrentTime());
    }}

    function updateTranscript(time) {{
      const idx = findSegmentIndex(time);
      document.querySelectorAll('#transcriptList .transcript-item').forEach(el => {{
        const i = parseInt(el.getAttribute('data-index'), 10);
        el.classList.toggle('current', i === idx);
      }});
    }}

    renderTranscriptList();

    document.querySelectorAll('.highlight-ts').forEach(el => {{
      el.addEventListener('click', () => {{
        const sec = parseFloat(el.getAttribute('data-seek'));
        if (player && player.seekTo && !isNaN(sec)) player.seekTo(sec, true);
      }});
      el.addEventListener('keydown', (e) => {{
        if (e.key === 'Enter' || e.key === ' ') {{
          e.preventDefault();
          const sec = parseFloat(el.getAttribute('data-seek'));
          if (player && player.seekTo && !isNaN(sec)) player.seekTo(sec, true);
        }}
      }});
    }});

    function onYouTubeIframeAPIReady() {{
      player = new YT.Player('player', {{
        height: '100%',
        width: '100%',
        videoId: '{video_id}',
        host: 'https://www.youtube-nocookie.com',
        playerVars: {{ autoplay: 0 }},
        events: {{
          onReady: function() {{
            pollInterval = setInterval(function() {{
              if (player && player.getCurrentTime) {{
                const t = player.getCurrentTime();
                if (typeof t === 'number' && !isNaN(t)) updateTranscript(t);
              }}
            }}, 300);
          }}
        }}
      }});
    }}

    if (window.location.protocol === 'file:') {{
      document.getElementById('fileProtocolNotice').style.display = 'block';
    }}
    initTheme();
    updateTranscript(0);
  </script>
</body>
</html>'''


def main():
    summary_overview = ""
    summary_overview_vi = ""
    summary_highlights = []
    channel_title = ""
    channel_id = ""
    published_at = ""
    duration_seconds = None
    if len(sys.argv) >= 5:
        video_id = sys.argv[1]
        video_title = sys.argv[2]
        transcript_raw = sys.argv[3]
        summary = sys.argv[4]
        summary_overview = summary
        output_dir = sys.argv[5] if len(sys.argv) > 5 else f"output/{video_id}"
    else:
        # Read from stdin as JSON
        try:
            data = json.load(sys.stdin)
            video_id = data["video_id"]
            video_title = data.get("video_title", "YouTube Video")
            transcript_raw = json.dumps(data.get("transcript", []))
            summary = data.get("summary", "")
            summary_overview = data.get("summary_overview", "")
            summary_overview_vi = data.get("summary_overview_vi", "")
            summary_highlights = data.get("summary_highlights", [])
            channel_title = data.get("channel_title", "")
            channel_id = data.get("channel_id", "")
            published_at = data.get("published_at", "")
            duration_seconds = data.get("duration_seconds")
            output_dir = data.get("output_dir", f"output/{video_id}")
        except (json.JSONDecodeError, KeyError) as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            sys.exit(1)

    try:
        transcript = json.loads(transcript_raw) if isinstance(transcript_raw, str) else transcript_raw
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}), file=sys.stderr)
        sys.exit(1)

    # Build metadata for metadata.json
    overview = summary_overview or summary
    if isinstance(summary_highlights, list):
        highlights = summary_highlights
    elif isinstance(summary_highlights, str) and summary_highlights.strip():
        highlights = [s.strip() for s in summary_highlights.strip().split("\n") if s.strip()]
    else:
        highlights = []
    dur_sec = duration_seconds
    if dur_sec is None and transcript:
        last = transcript[-1]
        dur_sec = int(last["start"] + last["duration"])
    metadata = {
        "video_id": video_id,
        "video_title": video_title,
        "channel_title": channel_title or "",
        "channel_id": channel_id or "",
        "published_at": published_at or "",
        "duration_seconds": dur_sec or 0,
        "sub_lines": len(transcript),
        "num_events": len(highlights),
        "summary_overview": overview or "",
        "summary_overview_vi": summary_overview_vi or "",
        "summary_highlights": highlights,
    }

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    # No longer copy player.html - use single player at project root: player.html?dir=output/xxx

    # Update output/README.md index
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    update_script = project_root / "scripts" / "update_output_index.py"
    if update_script.exists():
        subprocess.run(
            [
                sys.executable,
                str(update_script),
                "--type", "youtube",
                "--output-dir", str(out_path),
                "--title", video_title,
            ],
            cwd=str(project_root),
            capture_output=True,
        )

    try:
        rel_dir = str(out_path.resolve().relative_to(project_root.resolve()))
    except (ValueError, TypeError):
        rel_dir = str(out_path)
    print(json.dumps({"output_dir": str(out_path), "player_url": f"player.html?dir={rel_dir}"}))


if __name__ == "__main__":
    main()
