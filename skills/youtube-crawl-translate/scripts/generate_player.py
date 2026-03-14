#!/usr/bin/env python3
"""
Generate YouTube player HTML with transcript sync, dark mode, agentic UI.
Usage: python generate_player.py <video_id> <video_title> <transcript_json> <summary> <output_dir>
Or: pass args via stdin as JSON object: {video_id, video_title, transcript, summary, output_dir}
"""
import json
import html
import re
import sys
from pathlib import Path


def escape_js(s):
    """Escape string for use in JavaScript."""
    return json.dumps(s, ensure_ascii=False)


def build_html(
    video_id: str,
    video_title: str,
    transcript: list,
    summary: str = "",
    summary_overview: str = "",
    summary_highlights: list | str = "",
) -> str:
    """Build full HTML document."""
    transcript_js = json.dumps(transcript, ensure_ascii=False)
    title_esc = html.escape(video_title)
    overview = summary_overview or summary
    overview_esc = html.escape(overview).replace("\n", "<br>") if overview else ""
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
      --bg: #f8fafc;
      --surface: #ffffff;
      --text: #1e293b;
      --text-muted: #64748b;
      --accent: #3b82f6;
      --border: #e2e8f0;
      --highlight: #eff6ff;
    }}

    [data-theme="dark"] {{
      --bg: #0f172a;
      --surface: #1e293b;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #60a5fa;
      --border: #334155;
      --highlight: #1e3a5f;
    }}

    @media (prefers-color-scheme: dark) {{
      :root:not([data-theme="light"]) {{
        --bg: #0f172a;
        --surface: #1e293b;
        --text: #f1f5f9;
        --text-muted: #94a3b8;
        --accent: #60a5fa;
        --border: #334155;
        --highlight: #1e3a5f;
      }}
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

    .container {{ max-width: 960px; margin: 0 auto; padding: 1.5rem 0; }}

    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      gap: 1rem;
    }}

    h1 {{
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0;
      flex: 1;
      min-width: 0;
    }}

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

    .theme-toggle svg {{
      width: 20px;
      height: 20px;
    }}

    .theme-toggle .icon-moon {{ display: none; }}
    .theme-toggle .icon-sun {{ display: block; }}
    [data-theme="dark"] .theme-toggle .icon-sun {{ display: none; }}
    [data-theme="dark"] .theme-toggle .icon-moon {{ display: block; }}

    .theme-toggle:hover {{
      background: var(--highlight);
    }}

    .theme-toggle:focus-visible {{
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }}

    .watch-row {{
      display: grid;
      grid-template-columns: 55fr 45fr;
      gap: 1.5rem;
      margin-bottom: 1.5rem;
    }}

    @media (max-width: 767px) {{
      body {{ padding: 0 1rem; }}
      .watch-row {{
        grid-template-columns: 1fr;
      }}
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

    .transcript-line {{
      font-size: 0.95rem;
      color: var(--text);
      margin-bottom: 0.35rem;
      line-height: 1.5;
    }}

    .transcript-line.dim {{
      opacity: 0.6;
    }}

    .transcript-line.current {{
      font-weight: 500;
      color: var(--accent);
    }}

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
    <header>
      <h1>{title_esc}</h1>
      <button class="theme-toggle" id="themeToggle" aria-label="Toggle dark mode">
        <svg class="icon-sun" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        <svg class="icon-moon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      </button>
    </header>

    <div class="watch-row">
      <div class="video-wrap">
        <div id="player"></div>
        <div id="fileProtocolNotice" class="file-notice" style="display:none">
          Video không hiển thị khi mở file trực tiếp. Chạy: <code>python -m http.server 8080</code> rồi mở <code>http://localhost:8080/player.html</code>
        </div>
      </div>

      <div class="transcript-card">
        <h2>Transcript (sync)</h2>
        <div class="transcript-header">
          <button class="lang-chip active" id="langVi" aria-label="Xem phụ đề tiếng Việt">VI</button>
          <button class="lang-chip" id="langEn" aria-label="View English subtitles">EN</button>
        </div>
        <div class="transcript-area">
          <div class="transcript-line dim" id="transcriptPrev">—</div>
          <div class="transcript-line current" id="transcriptCurrent">—</div>
          <div class="transcript-line dim" id="transcriptNext">—</div>
        </div>
      </div>
    </div>

    <div class="summary-card">
      <h2>Tóm tắt</h2>
      <div class="summary-text" id="summary">
        {f'<div class="summary-overview">{overview_esc}</div>' if overview_esc else ''}
        {f'<h3 style="font-size:0.9rem;font-weight:600;margin:0 0 0.5rem 0;">Các phần đáng chú ý</h3><ul class="summary-highlights">{highlights_html}</ul>' if highlights_html else ''}
        {'' if (overview_esc or highlights_html) else '<span class="empty">Chưa có tóm tắt</span>'}
      </div>
    </div>
  </div>

  <script src="https://www.youtube.com/iframe_api"></script>
  <script>
    const transcriptData = {transcript_js};
    let player;
    let pollInterval;

    function initTheme() {{
      const saved = localStorage.getItem('yt-player-theme');
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const theme = saved || (prefersDark ? 'dark' : 'light');
      document.documentElement.setAttribute('data-theme', theme);
    }}

    document.getElementById('themeToggle').addEventListener('click', () => {{
      const current = document.documentElement.getAttribute('data-theme');
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
    const savedLang = localStorage.getItem(langKey) || 'vi';
    let showVi = savedLang === 'vi';
    document.getElementById('langVi').classList.toggle('active', showVi);
    document.getElementById('langEn').classList.toggle('active', !showVi);

    document.getElementById('langVi').addEventListener('click', () => {{
      showVi = true;
      document.getElementById('langVi').classList.add('active');
      document.getElementById('langEn').classList.remove('active');
      localStorage.setItem(langKey, 'vi');
      if (player && player.getCurrentTime) updateTranscript(player.getCurrentTime());
    }});
    document.getElementById('langEn').addEventListener('click', () => {{
      showVi = false;
      document.getElementById('langEn').classList.add('active');
      document.getElementById('langVi').classList.remove('active');
      localStorage.setItem(langKey, 'en');
      if (player && player.getCurrentTime) updateTranscript(player.getCurrentTime());
    }});

    function getSegmentText(seg) {{
      const text = seg.text || '—';
      const textVi = seg.textVi || '';
      return showVi && textVi ? textVi : text;
    }}

    function updateTranscript(time) {{
      const idx = findSegmentIndex(time);
      const prevEl = document.getElementById('transcriptPrev');
      const curEl = document.getElementById('transcriptCurrent');
      const nextEl = document.getElementById('transcriptNext');
      if (idx >= 0) {{
        curEl.textContent = getSegmentText(transcriptData[idx]);
        prevEl.textContent = idx > 0 ? getSegmentText(transcriptData[idx - 1]) : '—';
        nextEl.textContent = idx < transcriptData.length - 1 ? getSegmentText(transcriptData[idx + 1]) : '—';
      }} else {{
        prevEl.textContent = '—';
        curEl.textContent = '—';
        nextEl.textContent = '—';
      }}
    }}

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
    if len(sys.argv) >= 5:
        video_id = sys.argv[1]
        video_title = sys.argv[2]
        transcript_raw = sys.argv[3]
        summary = sys.argv[4]
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
            summary_highlights = data.get("summary_highlights", [])
            output_dir = data.get("output_dir", f"output/{video_id}")
        except (json.JSONDecodeError, KeyError) as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            sys.exit(1)

    try:
        transcript = json.loads(transcript_raw) if isinstance(transcript_raw, str) else transcript_raw
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}), file=sys.stderr)
        sys.exit(1)

    html_content = build_html(
        video_id, video_title, transcript,
        summary=summary,
        summary_overview=summary_overview,
        summary_highlights=summary_highlights,
    )

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "player.html").write_text(html_content, encoding="utf-8")

    print(json.dumps({"output": str(out_path / "player.html")}))


if __name__ == "__main__":
    main()
