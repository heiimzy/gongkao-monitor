#!/usr/bin/env python3
"""
从 announcements.json 生成 GitHub Pages 静态页面 v3
- 去重（按 URL 去重）
- 分页加载（每页 20 条）
- 类型筛选（公告/公示/招考/其他）
- 内容直接展示
"""
import json
import os
import re
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


def deduplicate(announcements):
    """按 URL 去重，保留第一个（通常是国考来源）"""
    seen_urls = set()
    deduped = []
    for a in announcements:
        url = a.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            deduped.append(a)
    return deduped


def classify_announcement(title):
    """根据标题分类公告类型"""
    if "公示" in title or "拟录用" in title:
        return "公示"
    elif "公告" in title:
        return "公告"
    elif "招考" in title or "招录" in title:
        return "招考"
    elif "报名" in title:
        return "报名"
    elif "面试" in title:
        return "面试"
    elif "笔试" in title or "成绩" in title or "分数" in title:
        return "笔试"
    elif "职位" in title:
        return "职位"
    else:
        return "其他"


def type_color(t):
    return {
        "公告": "#e74c3c",
        "公示": "#f39c12",
        "招考": "#3498db",
        "报名": "#2ecc71",
        "面试": "#9b59b6",
        "笔试": "#1abc9c",
        "职位": "#e67e22",
        "其他": "#95a5a6",
    }.get(t, "#95a5a6")


def source_color(source):
    return {"国考": "#e74c3c", "省考": "#3498db", "华图": "#2ecc71"}.get(source, "#95a5a6")


def format_content(content):
    if not content:
        return '<p class="no-content">暂无详细内容，点击原文链接查看</p>'
    content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    paragraphs = content.split("\n")
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(p) < 50 and re.match(r'^[一二三四五六七八九十]+[、．.]', p):
            html_parts.append(f'<h4>{p}</h4>')
        elif re.match(r'^[（(][一二三四五六七八九十]+[）)]', p):
            html_parts.append(f'<p class="sub-item">{p}</p>')
        else:
            html_parts.append(f'<p>{p}</p>')
    return "\n".join(html_parts) if html_parts else '<p class="no-content">暂无详细内容</p>'


def generate_html(data):
    # Deduplicate
    announcements = deduplicate(data.get("announcements", []))
    last_update = data.get("last_update", "")
    total = len(announcements)
    
    # Classify
    for a in announcements:
        a["type"] = classify_announcement(a.get("title", ""))
    
    by_source = defaultdict(int)
    by_type = defaultdict(int)
    for a in announcements:
        by_source[a.get("source", "未知")] += 1
        by_type[a["type"]] += 1
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Stats
    source_cards = ""
    for src, count in sorted(by_source.items(), key=lambda x: -x[1]):
        color = source_color(src)
        source_cards += f'<div class="stat-card" style="border-left: 4px solid {color}"><div class="stat-number">{count}</div><div class="stat-label">{src}</div></div>'
    
    type_cards = ""
    for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
        color = type_color(t)
        type_cards += f'<div class="stat-card" style="border-left: 4px solid {color}"><div class="stat-number">{count}</div><div class="stat-label">{t}</div></div>'

    # Announcement cards (all, with data attributes for filtering)
    all_cards = ""
    for a in announcements:
        color = source_color(a.get("source", ""))
        t = a.get("type", "其他")
        tc = type_color(t)
        content_html = format_content(a.get("content", ""))
        cid = f"c-{a['hash']}"
        has_content = bool(a.get("content") and len(a["content"]) > 50)
        
        all_cards += f'''<div class="announcement-card" data-source="{a.get("source","")}" data-type="{t}">
<div class="card-header" onclick="toggle('{cid}')">
<div class="card-left">
<span class="source-badge" style="background:{color}">{a.get("source","")}</span>
<span class="type-badge" style="background:{tc}">{t}</span>
<span class="card-title">{a.get("title","")}</span>
</div>
<span class="expand-icon" id="i-{cid}">▼</span>
</div>
<div class="card-meta">
<span>📅 {a.get("date_found","")[:10]}</span>
{f'<span>📰 {a["date_pub"]}</span>' if a.get("date_pub") else ""}
{"<span class='content-tag'>📄 有正文</span>" if has_content else ""}
<a href="{a.get("url","#")}" target="_blank" rel="noopener" class="original-link">原文 ↗</a>
</div>
<div class="card-content" id="{cid}" style="display:none">{content_html}</div>
</div>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>公考信息监控 | 自动更新</title>
<style>
:root{{--bg:#0f1419;--bg2:#1a1f2e;--card:#1e2538;--content:#161b26;--t1:#e8eaed;--t2:#8b95a5;--tm:#5f6b7a;--bd:#2a3040;--ac:#4a9eff;--glow:rgba(74,158,255,.15)}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--t1);line-height:1.7}}
.ctn{{max-width:900px;margin:0 auto;padding:20px}}
.hdr{{text-align:center;padding:40px 0 30px;border-bottom:1px solid var(--bd);margin-bottom:30px}}
.hdr h1{{font-size:28px;font-weight:700;margin-bottom:8px;background:linear-gradient(135deg,#4a9eff,#7c5cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.hdr .sub{{color:var(--t2);font-size:14px}}
.hdr .upd{{color:var(--tm);font-size:12px;margin-top:8px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:10px;margin-bottom:24px}}
.st{{background:var(--card);border-radius:10px;padding:14px;text-align:center}}
.st .n{{font-size:26px;font-weight:700}}.st .l{{font-size:12px;color:var(--t2);margin-top:2px}}
.srch{{width:100%;padding:12px 16px;background:var(--card);border:1px solid var(--bd);border-radius:10px;color:var(--t1);font-size:14px;margin-bottom:12px;outline:none}}
.srch:focus{{border-color:var(--ac)}}.srch::placeholder{{color:var(--tm)}}
.fb{{display:flex;gap:6px;margin-bottom:20px;flex-wrap:wrap}}
.fb button{{background:var(--card);border:1px solid var(--bd);color:var(--t2);padding:5px 14px;border-radius:18px;font-size:12px;cursor:pointer;transition:all .2s}}
.fb button:hover,.fb button.on{{background:var(--ac);color:#fff;border-color:var(--ac)}}
.fb .sep{{width:1px;background:var(--bd);margin:0 4px}}
.card{{background:var(--card);border-radius:10px;margin-bottom:6px;border:1px solid transparent;transition:all .2s}}
.card:hover{{border-color:var(--ac);box-shadow:0 0 16px var(--glow)}}
.card.hide{{display:none}}
.ch{{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;cursor:pointer;user-select:none}}
.ch:hover{{background:rgba(74,158,255,.04)}}
.cl{{display:flex;align-items:center;gap:8px;flex:1;min-width:0}}
.sb{{font-size:10px;font-weight:600;color:#fff;padding:2px 8px;border-radius:10px;white-space:nowrap}}
.tb{{font-size:10px;font-weight:500;color:#fff;padding:2px 6px;border-radius:8px;white-space:nowrap}}
.ct{{font-size:14px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.ei{{color:var(--tm);font-size:11px;transition:transform .2s;flex-shrink:0;margin-left:8px}}
.ei.op{{transform:rotate(180deg)}}
.cm{{display:flex;gap:14px;font-size:11px;color:var(--tm);padding:0 16px 10px;align-items:center;flex-wrap:wrap}}
.ol{{color:var(--ac);text-decoration:none;margin-left:auto}}.ol:hover{{text-decoration:underline}}
.ctag{{color:#2ecc71;font-size:11px}}
.cc{{padding:12px 16px;background:var(--content);margin:0 8px 8px;border-radius:8px;font-size:13px;line-height:1.8;color:var(--t2);max-height:400px;overflow-y:auto}}
.cc h4{{color:var(--t1);font-size:13px;font-weight:600;margin:10px 0 4px}}
.cc p{{margin-bottom:6px}}.cc p.si{{padding-left:18px}}
.nc{{color:var(--tm);font-style:italic;text-align:center;padding:16px}}
.pg{{display:flex;justify-content:center;gap:6px;margin:24px 0;flex-wrap:wrap}}
.pg button{{background:var(--card);border:1px solid var(--bd);color:var(--t2);padding:6px 12px;border-radius:6px;font-size:13px;cursor:pointer;transition:all .2s}}
.pg button:hover,.pg button.on{{background:var(--ac);color:#fff;border-color:var(--ac)}}
.pg button:disabled{{opacity:.4;cursor:default}}
.ft{{text-align:center;padding:30px 0;border-top:1px solid var(--bd);margin-top:30px;color:var(--tm);font-size:12px}}
.ft a{{color:var(--ac);text-decoration:none}}
.st{{position:fixed;bottom:24px;right:24px;width:40px;height:40px;background:var(--ac);border:none;border-radius:50%;color:#fff;font-size:18px;cursor:pointer;display:none;align-items:center;justify-content:center;z-index:100;box-shadow:0 4px 12px rgba(74,158,255,.3)}}
.st.v{{display:flex}}
.cnt{{text-align:center;color:var(--tm);font-size:13px;margin-bottom:16px}}
@media(max-width:600px){{.ctn{{padding:12px}}.hdr h1{{font-size:22px}}.stats{{grid-template-columns:repeat(3,1fr)}}.cl{{gap:6px}}.ct{{font-size:13px}}}}
</style>
</head>
<body>
<div class="ctn">
<div class="hdr">
<h1>🏛️ 公考信息监控</h1>
<p class="sub">自动追踪中公教育、华图教育等平台的公务员考试公告</p>
<p class="upd">最后更新：{last_update or now} | 每2小时自动更新 | 已去重</p>
</div>

<div class="stats">
<div class="st"><div class="n">{total}</div><div class="l">📋 总公告</div></div>
{source_cards}
{type_cards}
</div>

<input type="text" class="srch" id="search" placeholder="🔍 搜索公告标题..." oninput="doFilter()">

<div class="fb" id="filters">
<button class="on" data-filter="all" onclick="setFilter(this,'all')">全部</button>
<div class="sep"></div>
<button data-filter="source:国考" onclick="setFilter(this,'source:国考')">🔴 国考</button>
<button data-filter="source:省考" onclick="setFilter(this,'source:省考')">🔵 省考</button>
<button data-filter="source:华图" onclick="setFilter(this,'source:华图')">🟢 华图</button>
<div class="sep"></div>
<button data-filter="type:公告" onclick="setFilter(this,'type:公告')">📢 公告</button>
<button data-filter="type:公示" onclick="setFilter(this,'type:公示')">📋 公示</button>
<button data-filter="type:招考" onclick="setFilter(this,'type:招考')">🎯 招考</button>
<button data-filter="type:面试" onclick="setFilter(this,'type:面试')">🎤 面试</button>
<button data-filter="type:职位" onclick="setFilter(this,'type:职位')">💼 职位</button>
</div>

<div class="cnt" id="count"></div>
<div id="list">{all_cards}</div>
<div class="pg" id="pager"></div>

<div class="ft">
<p>数据来源：<a href="https://www.offcn.com/gwy/" target="_blank">中公教育</a> · <a href="https://www.huatu.com/gwy/" target="_blank">华图教育</a></p>
<p style="margin-top:4px">由 Hermes Agent 自动监控更新 · {now}</p>
</div>
</div>
<button class="st" id="st" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>
<script>
const PAGE_SIZE=20;let curPage=1,curFilter='all';
function toggle(id){{const e=document.getElementById(id),i=document.getElementById('i-'+id);if(e.style.display==='none'){{e.style.display='block';i.classList.add('op')}}else{{e.style.display='none';i.classList.remove('op')}}}}
function setFilter(btn,f){{document.querySelectorAll('.fb button').forEach(b=>b.classList.remove('on'));btn.classList.add('on');curFilter=f;curPage=1;doFilter()}}
function doFilter(){{const q=document.getElementById('search').value.toLowerCase();document.querySelectorAll('.card').forEach(c=>{{const src=c.dataset.source,typ=c.dataset.type,tit=c.querySelector('.ct').textContent.toLowerCase();let show=true;if(curFilter!=='all'){{if(curFilter.startsWith('source:'))show=src===curFilter.split(':')[1];else if(curFilter.startsWith('type:'))show=typ===curFilter.split(':')[1]}}if(q&&!tit.includes(q))show=false;c.classList.toggle('hide',!show)}});renderPage()}}
function renderPage(){{const cards=[...document.querySelectorAll('.card:not(.hide)')];const total=cards.length;const pages=Math.ceil(total/PAGE_SIZE);if(curPage>pages)curPage=pages||1;const start=(curPage-1)*PAGE_SIZE;cards.forEach((c,i)=>{{c.style.display=(i>=start&&i<start+PAGE_SIZE)?'':'none'}});document.getElementById('count').textContent=`显示 ${{start+1}}-${{Math.min(start+PAGE_SIZE,total)}}/${{total}} 条`;let pg='';if(pages>1){{pg+=`<button ${{curPage===1?'disabled':''}} onclick="goPage(${{curPage-1}})">‹</button>`;const range=[];for(let i=1;i<=pages;i++){{if(i===1||i===pages||Math.abs(i-curPage)<=2)range.push(i);else if(range[range.length-1]!=='...')range.push('...')}}range.forEach(p=>{{if(p==='...')pg+=`<button disabled>...</button>`;else pg+=`<button class="${{p===curPage?'on':''}}" onclick="goPage(${{p}})">${{p}}</button>`}});pg+=`<button ${{curPage===pages?'disabled':''}} onclick="goPage(${{curPage+1}})">›</button>`}}document.getElementById('pager').innerHTML=pg}}
function goPage(p){{curPage=p;renderPage();window.scrollTo({{top:200,behavior:'smooth'}})}}
window.addEventListener('scroll',()=>{{document.getElementById('st').classList.toggle('v',window.scrollY>300)}});
doFilter();
</script>
</body>
</html>'''
    return html


def main():
    data = load_announcements()
    before = len(data.get("announcements", []))
    html = generate_html(data)
    data["announcements"] = deduplicate(data.get("announcements", []))
    after = len(data["announcements"])
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ 页面已生成: {OUTPUT_FILE}")
    print(f"   原始: {before} 条 → 去重后: {after} 条")
    print(f"   最后更新: {data.get('last_update', '')}")


if __name__ == "__main__":
    main()
