#!/usr/bin/env python3
"""
从 announcements.json 生成 GitHub Pages 静态页面
"""
import json
import os
from datetime import datetime
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ANNOUNCEMENTS_FILE = os.path.join(DATA_DIR, "announcements.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "index.html")


def load_announcements():
    if os.path.exists(ANNOUNCEMENTS_FILE):
        with open(ANNOUNCEMENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"announcements": [], "last_update": "", "total": 0}


def group_by_date(announcements):
    groups = defaultdict(list)
    for a in announcements:
        date = a.get("date_found", "")[:10] or "未知日期"
        groups[date].append(a)
    return dict(sorted(groups.items(), reverse=True))


def group_by_source(announcements):
    counts = defaultdict(int)
    for a in announcements:
        counts[a.get("source", "未知")] += 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def source_color(source):
    colors = {
        "国考": "#e74c3c",
        "省考": "#3498db",
        "华图": "#2ecc71",
    }
    return colors.get(source, "#95a5a6")


def generate_html(data):
    announcements = data.get("announcements", [])
    last_update = data.get("last_update", "")
    total = data.get("total", len(announcements))
    
    by_date = group_by_date(announcements)
    by_source = group_by_source(announcements)
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Build source stats cards
    source_cards = ""
    for src, count in by_source.items():
        color = source_color(src)
        source_cards += f'''
        <div class="stat-card" style="border-left: 4px solid {color}">
            <div class="stat-number">{count}</div>
            <div class="stat-label">{src}</div>
        </div>'''

    # Build announcement list by date
    date_sections = ""
    for date, items in by_date.items():
        cards = ""
        for item in items:
            color = source_color(item.get("source", ""))
            cards += f'''
            <div class="announcement-card">
                <div class="card-header">
                    <span class="source-badge" style="background: {color}">{item.get("source", "")}</span>
                    <span class="card-date">{item.get("date_found", "")[:10]}</span>
                </div>
                <a href="{item.get("url", "#")}" target="_blank" rel="noopener" class="card-title">{item.get("title", "")}</a>
                <div class="card-meta">
                    <span>📅 发现于 {item.get("date_found", "")}</span>
                    {f'<span>📰 发布于 {item["date_pub"]}</span>' if item.get("date_pub") else ""}
                </div>
            </div>'''
        
        date_sections += f'''
        <div class="date-group">
            <h2 class="date-heading">📅 {date} <span class="date-count">{len(items)} 条</span></h2>
            {cards}
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>公考信息监控 | 自动更新</title>
    <meta name="description" content="公务员考试公告自动监控，实时追踪中公、华图等平台的最新招考信息">
    <style>
        :root {{
            --bg-primary: #0f1419;
            --bg-secondary: #1a1f2e;
            --bg-card: #1e2538;
            --text-primary: #e8eaed;
            --text-secondary: #8b95a5;
            --text-muted: #5f6b7a;
            --border: #2a3040;
            --accent: #4a9eff;
            --accent-glow: rgba(74, 158, 255, 0.15);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Header */
        .header {{
            text-align: center;
            padding: 40px 0 30px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 30px;
        }}

        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #4a9eff, #7c5cff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .header .subtitle {{
            color: var(--text-secondary);
            font-size: 14px;
        }}

        .header .update-info {{
            color: var(--text-muted);
            font-size: 12px;
            margin-top: 8px;
        }}

        /* Stats */
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: var(--bg-card);
            border-radius: 10px;
            padding: 16px;
            text-align: center;
        }}

        .stat-number {{
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .stat-label {{
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 4px;
        }}

        /* Date groups */
        .date-group {{
            margin-bottom: 24px;
        }}

        .date-heading {{
            font-size: 16px;
            font-weight: 600;
            color: var(--text-secondary);
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .date-count {{
            font-size: 12px;
            font-weight: 400;
            color: var(--text-muted);
            background: var(--bg-secondary);
            padding: 2px 8px;
            border-radius: 10px;
        }}

        /* Cards */
        .announcement-card {{
            background: var(--bg-card);
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 8px;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }}

        .announcement-card:hover {{
            border-color: var(--accent);
            box-shadow: 0 0 20px var(--accent-glow);
            transform: translateY(-1px);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .source-badge {{
            font-size: 11px;
            font-weight: 600;
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .card-date {{
            font-size: 12px;
            color: var(--text-muted);
        }}

        .card-title {{
            display: block;
            font-size: 15px;
            font-weight: 500;
            color: var(--text-primary);
            text-decoration: none;
            line-height: 1.5;
            margin-bottom: 8px;
        }}

        .card-title:hover {{
            color: var(--accent);
        }}

        .card-meta {{
            display: flex;
            gap: 16px;
            font-size: 12px;
            color: var(--text-muted);
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px 0;
            border-top: 1px solid var(--border);
            margin-top: 30px;
            color: var(--text-muted);
            font-size: 12px;
        }}

        .footer a {{
            color: var(--accent);
            text-decoration: none;
        }}

        /* Filter bar */
        .filter-bar {{
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .filter-btn:hover, .filter-btn.active {{
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }}

        /* Search */
        .search-box {{
            width: 100%;
            padding: 12px 16px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text-primary);
            font-size: 14px;
            margin-bottom: 20px;
            outline: none;
            transition: border-color 0.2s;
        }}

        .search-box:focus {{
            border-color: var(--accent);
        }}

        .search-box::placeholder {{
            color: var(--text-muted);
        }}

        /* Responsive */
        @media (max-width: 600px) {{
            .container {{
                padding: 12px;
            }}
            .header h1 {{
                font-size: 22px;
            }}
            .stats {{
                grid-template-columns: repeat(2, 1fr);
            }}
            .card-meta {{
                flex-direction: column;
                gap: 4px;
            }}
        }}

        /* Scroll to top */
        .scroll-top {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 40px;
            height: 40px;
            background: var(--accent);
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 18px;
            cursor: pointer;
            display: none;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(74, 158, 255, 0.3);
            z-index: 100;
        }}

        .scroll-top.visible {{
            display: flex;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ 公考信息监控</h1>
            <p class="subtitle">自动追踪中公教育、华图教育等平台的公务员考试公告</p>
            <p class="update-info">最后更新：{last_update or now} | 自动更新频率：每2小时</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total}</div>
                <div class="stat-label">📋 总公告数</div>
            </div>
            {source_cards}
            <div class="stat-card">
                <div class="stat-number">2h</div>
                <div class="stat-label">⏱️ 更新频率</div>
            </div>
        </div>

        <input type="text" class="search-box" id="search" placeholder="🔍 搜索公告标题..." oninput="filterAnnouncements()">

        <div class="filter-bar">
            <button class="filter-btn active" onclick="filterSource('all', this)">全部</button>
            <button class="filter-btn" onclick="filterSource('国考', this)" style="--accent-color: #e74c3c">🔴 国考</button>
            <button class="filter-btn" onclick="filterSource('省考', this)" style="--accent-color: #3498db">🔵 省考</button>
            <button class="filter-btn" onclick="filterSource('华图', this)" style="--accent-color: #2ecc71">🟢 华图</button>
        </div>

        <div id="announcements">
            {date_sections}
        </div>

        <div class="footer">
            <p>数据来源：<a href="https://www.offcn.com/gwy/" target="_blank">中公教育</a> · <a href="https://www.huatu.com/gwy/" target="_blank">华图教育</a></p>
            <p style="margin-top: 4px">由 Hermes Agent 自动监控更新 · {now}</p>
        </div>
    </div>

    <button class="scroll-top" id="scrollTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>

    <script>
        // Scroll to top button
        window.addEventListener('scroll', () => {{
            const btn = document.getElementById('scrollTop');
            btn.classList.toggle('visible', window.scrollY > 300);
        }});

        // Source filter
        function filterSource(source, btn) {{
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            document.querySelectorAll('.announcement-card').forEach(card => {{
                const badge = card.querySelector('.source-badge');
                if (source === 'all' || badge.textContent === source) {{
                    card.style.display = '';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
            
            // Show/hide date groups with no visible cards
            document.querySelectorAll('.date-group').forEach(group => {{
                const visibleCards = group.querySelectorAll('.announcement-card:not([style*="display: none"])');
                group.style.display = visibleCards.length > 0 ? '' : 'none';
            }});
        }}

        // Search filter
        function filterAnnouncements() {{
            const query = document.getElementById('search').value.toLowerCase();
            document.querySelectorAll('.announcement-card').forEach(card => {{
                const title = card.querySelector('.card-title').textContent.toLowerCase();
                card.style.display = title.includes(query) ? '' : 'none';
            }});
            
            document.querySelectorAll('.date-group').forEach(group => {{
                const visibleCards = group.querySelectorAll('.announcement-card:not([style*="display: none"])');
                group.style.display = visibleCards.length > 0 ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>'''
    return html


def main():
    data = load_announcements()
    html = generate_html(data)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ 页面已生成: {OUTPUT_FILE}")
    print(f"   总公告数: {data.get('total', 0)}")
    print(f"   最后更新: {data.get('last_update', '')}")


if __name__ == "__main__":
    main()
