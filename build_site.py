#!/usr/bin/env python3
"""
站点生成器 v4
- index.html: 分页列表页
- articles/{hash}.html: 文章独立页面
"""
import json, os, re, hashlib
from datetime import datetime
from collections import defaultdict
from xml.sax.saxutils import escape as xml_escape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ARTICLES_DIR = os.path.join(BASE_DIR, "articles")
ANN_FILE = os.path.join(DATA_DIR, "announcements.json")

PAGE_SIZE = 20


def load_data():
    with open(ANN_FILE) as f:
        return json.load(f)


def deduplicate(announcements):
    seen = set()
    result = []
    for a in announcements:
        url = a.get("url", "")
        if url not in seen:
            seen.add(url)
            result.append(a)
    return result


def classify(title):
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
    return "其他"


def type_color(t):
    return {"公告":"#e74c3c","公示":"#f39c12","招考":"#3498db","报名":"#2ecc71",
            "面试":"#9b59b6","笔试":"#1abc9c","职位":"#e67e22","其他":"#95a5a6"}.get(t,"#95a5a6")


def source_color(s):
    return {"国考":"#e74c3c","省考":"#3498db","华图":"#2ecc71"}.get(s,"#95a5a6")


def format_article_content(content):
    if not content:
        return "<p>暂无详细内容</p>"
    content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = content.split("\n")
    html = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if len(line) < 50 and re.match(r'^[一二三四五六七八九十]+[、．.]', line):
            html.append(f"<h3>{line}</h3>")
        elif re.match(r'^[（(][一二三四五六七八九十]+[）)]', line):
            html.append(f'<p class="sub-item">{line}</p>')
        elif re.match(r'^\d+[.、]', line):
            html.append(f'<p class="list-item">{line}</p>')
        else:
            html.append(f"<p>{line}</p>")
    return "\n".join(html) if html else "<p>暂无详细内容</p>"


# ─── Article page template ───

def article_page(a, all_articles):
    """生成单篇文章页面"""
    content_html = format_article_content(a.get("content", ""))
    t = a.get("type", "其他")
    tc = type_color(t)
    sc = source_color(a.get("source", ""))
    
    # Prev/Next navigation
    idx = next((i for i, x in enumerate(all_articles) if x["hash"] == a["hash"]), 0)
    prev_a = all_articles[idx + 1] if idx + 1 < len(all_articles) else None
    next_a = all_articles[idx - 1] if idx - 1 >= 0 else None
    
    nav = '<div class="nav-row">'
    if prev_a:
        nav += f'<a href="{prev_a["hash"]}.html" class="nav-btn">‹ {prev_a["title"][:30]}</a>'
    else:
        nav += '<span class="nav-btn disabled">‹ 上一篇</span>'
    nav += f'<a href="../index.html" class="nav-btn">📋 目录</a>'
    if next_a:
        nav += f'<a href="{next_a["hash"]}.html" class="nav-btn">{next_a["title"][:30]} ›</a>'
    else:
        nav += '<span class="nav-btn disabled">下一篇 ›</span>'
    nav += '</div>'
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{a.get("title","")} - 公考信息监控</title>
<link rel="alternate" type="application/rss+xml" title="RSS" href="../rss.xml">
<style>
:root{{--bg:#0f1419;--bg2:#1a1f2e;--card:#1e2538;--content:#161b26;--t1:#e8eaed;--t2:#8b95a5;--tm:#5f6b7a;--bd:#2a3040;--ac:#4a9eff}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--t1);line-height:1.8}}
.w{{max-width:800px;margin:0 auto;padding:20px}}
a{{color:var(--ac);text-decoration:none}}a:hover{{text-decoration:underline}}
.back{{display:inline-block;margin-bottom:20px;font-size:14px;color:var(--ac)}}
.hdr{{margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid var(--bd)}}
.hdr h1{{font-size:24px;font-weight:700;margin-bottom:12px;line-height:1.4}}
.meta{{display:flex;gap:12px;font-size:13px;color:var(--tm);flex-wrap:wrap;align-items:center}}
.badge{{font-size:11px;font-weight:600;color:#fff;padding:2px 8px;border-radius:10px}}
.article-body{{background:var(--card);border-radius:12px;padding:24px 28px;font-size:15px;line-height:1.9;color:var(--t2)}}
.article-body h3{{color:var(--t1);font-size:17px;font-weight:600;margin:20px 0 8px}}
.article-body p{{margin-bottom:10px}}
.article-body p.sub-item{{padding-left:20px}}
.article-body p.list-item{{padding-left:8px;border-left:2px solid var(--ac);margin-left:4px}}
.nav-row{{display:flex;justify-content:space-between;gap:8px;margin-top:24px;flex-wrap:wrap}}
.nav-btn{{background:var(--card);border:1px solid var(--bd);color:var(--t2);padding:8px 16px;border-radius:8px;font-size:13px;text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:45%}}
.nav-btn:hover{{border-color:var(--ac);color:var(--ac);text-decoration:none}}
.nav-btn.disabled{{opacity:.3;cursor:default}}
.ft{{text-align:center;padding:30px 0;color:var(--tm);font-size:12px;border-top:1px solid var(--bd);margin-top:30px}}
@media(max-width:600px){{.w{{padding:14px}}.hdr h1{{font-size:20px}}.article-body{{padding:16px;font-size:14px}}}}
</style>
</head>
<body>
<div class="w">
<a href="../index.html" class="back">← 返回目录</a>
<div class="hdr">
<h1>{a.get("title","")}</h1>
<div class="meta">
<span class="badge" style="background:{sc}">{a.get("source","")}</span>
<span class="badge" style="background:{tc}">{t}</span>
<span>📅 抓取于 {a.get("date_found","")[:10]}</span>
{f'<span>📰 发布于 {a["date_pub"]}</span>' if a.get("date_pub") else ""}
<a href="../rss.xml" target="_blank" rel="noopener">📡 RSS</a>
<a href="{a.get("url","#")}" target="_blank" rel="noopener">原文链接 ↗</a>
</div>
</div>
<div class="article-body">{content_html}</div>
{nav}
<div class="ft">由 Hermes Agent 自动监控更新 · {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
</div>
</body>
</html>'''


# ─── Index page template ───

def index_page(articles, page, total_pages, last_update):
    """生成列表页"""
    start = (page - 1) * PAGE_SIZE
    page_items = articles[start:start + PAGE_SIZE]
    
    # Stats
    by_source = defaultdict(int)
    by_type = defaultdict(int)
    for a in articles:
        by_source[a.get("source", "?")] += 1
        by_type[a.get("type", "其他")] += 1
    
    source_cards = "".join(
        f'<div class="st" style="border-left:4px solid {source_color(s)}"><div class="n">{c}</div><div class="l">{s}</div></div>'
        for s, c in sorted(by_source.items(), key=lambda x: -x[1])
    )
    type_cards = "".join(
        f'<div class="st" style="border-left:4px solid {type_color(t)}"><div class="n">{c}</div><div class="l">{t}</div></div>'
        for t, c in sorted(by_type.items(), key=lambda x: -x[1])
    )
    
    # Cards
    cards = ""
    for a in page_items:
        sc = source_color(a.get("source", ""))
        t = a.get("type", "其他")
        tc = type_color(t)
        has_content = bool(a.get("content") and len(a["content"]) > 80)
        cards += f'''<div class="card" data-source="{a.get("source","")}" data-type="{t}">
<a href="articles/{a["hash"]}.html" class="card-link">
<div class="ch">
<div class="cl">
<span class="sb" style="background:{sc}">{a.get("source","")}</span>
<span class="tb" style="background:{tc}">{t}</span>
<span class="ct">{a.get("title","")}</span>
</div>
<span class="ei">›</span>
</div>
<div class="cm">
<span>📅 {a.get("date_found","")[:10]}</span>
{f'<span>📰 {a["date_pub"]}</span>' if a.get("date_pub") else ""}
{"<span class='ctag'>📄 有正文</span>" if has_content else '<span class="ctag dim">无正文</span>'}
</div>
</a>
</div>'''
    
    # Pagination
    pager = ""
    if total_pages > 1:
        pager = '<div class="pg">'
        if page > 1:
            pager += f'<a href="?page={page-1}" class="pb">‹ 上一页</a>'
        for p in range(1, total_pages + 1):
            if p == 1 or p == total_pages or abs(p - page) <= 2:
                cls = "pb on" if p == page else "pb"
                pager += f'<a href="?page={p}" class="{cls}">{p}</a>'
            elif pager.endswith('<span class="pb">...</span>') == False:
                pager += '<span class="pb">...</span>'
        if page < total_pages:
            pager += f'<a href="?page={page+1}" class="pb">下一页 ›</a>'
        pager += '</div>'
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>公考信息监控 | 自动更新</title>
<link rel="alternate" type="application/rss+xml" title="RSS" href="rss.xml">
<style>
:root{{--bg:#0f1419;--bg2:#1a1f2e;--card:#1e2538;--t1:#e8eaed;--t2:#8b95a5;--tm:#5f6b7a;--bd:#2a3040;--ac:#4a9eff;--glow:rgba(74,158,255,.15)}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--t1);line-height:1.7}}
.ctn{{max-width:900px;margin:0 auto;padding:20px}}
.hdr{{text-align:center;padding:40px 0 30px;border-bottom:1px solid var(--bd);margin-bottom:30px}}
.hdr h1{{font-size:28px;font-weight:700;background:linear-gradient(135deg,#4a9eff,#7c5cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:8px}}
.hdr .sub{{color:var(--t2);font-size:14px}}.hdr .upd{{color:var(--tm);font-size:12px;margin-top:8px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:8px;margin-bottom:24px}}
.st{{background:var(--card);border-radius:8px;padding:12px;text-align:center}}
.st .n{{font-size:22px;font-weight:700}}.st .l{{font-size:11px;color:var(--t2);margin-top:2px}}
.srch{{width:100%;padding:11px 14px;background:var(--card);border:1px solid var(--bd);border-radius:8px;color:var(--t1);font-size:14px;margin-bottom:10px;outline:none}}
.srch:focus{{border-color:var(--ac)}}.srch::placeholder{{color:var(--tm)}}
.fb{{display:flex;gap:5px;margin-bottom:16px;flex-wrap:wrap;align-items:center}}
.fb a{{background:var(--card);border:1px solid var(--bd);color:var(--t2);padding:4px 12px;border-radius:16px;font-size:11px;text-decoration:none;transition:all .2s}}
.fb a:hover,.fb a.on{{background:var(--ac);color:#fff;border-color:var(--ac)}}
.fb .sep{{width:1px;height:16px;background:var(--bd);margin:0 2px}}
.card{{background:var(--card);border-radius:8px;margin-bottom:4px;border:1px solid transparent;transition:all .2s}}
.card:hover{{border-color:var(--ac);box-shadow:0 0 12px var(--glow)}}
.card.hide{{display:none}}
.card-link{{display:block;text-decoration:none;color:inherit}}
.card-link:hover{{text-decoration:none}}
.ch{{display:flex;justify-content:space-between;align-items:center;padding:10px 14px}}
.cl{{display:flex;align-items:center;gap:6px;flex:1;min-width:0}}
.sb{{font-size:10px;font-weight:600;color:#fff;padding:2px 7px;border-radius:8px;white-space:nowrap}}
.tb{{font-size:10px;font-weight:500;color:#fff;padding:2px 5px;border-radius:6px;white-space:nowrap}}
.ct{{font-size:14px;color:var(--t1);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.ei{{color:var(--tm);font-size:16px;flex-shrink:0;margin-left:6px}}
.cm{{display:flex;gap:12px;font-size:11px;color:var(--tm);padding:0 14px 8px;flex-wrap:wrap;align-items:center}}
.ctag{{color:#2ecc71;font-size:11px}}.ctag.dim{{color:var(--tm);font-style:italic}}
.pg{{display:flex;justify-content:center;gap:4px;margin:20px 0;flex-wrap:wrap}}
.pb{{background:var(--card);border:1px solid var(--bd);color:var(--t2);padding:5px 10px;border-radius:5px;font-size:12px;text-decoration:none;display:inline-block}}
.pb:hover,.pb.on{{background:var(--ac);color:#fff;border-color:var(--ac)}}
.cnt{{text-align:center;color:var(--tm);font-size:12px;margin-bottom:12px}}
.ft{{text-align:center;padding:24px 0;border-top:1px solid var(--bd);margin-top:24px;color:var(--tm);font-size:12px}}
.ft a{{color:var(--ac);text-decoration:none}}
@media(max-width:600px){{.ctn{{padding:12px}}.hdr h1{{font-size:22px}}.stats{{grid-template-columns:repeat(3,1fr)}}}}
</style>
</head>
<body>
<div class="ctn">
<div class="hdr">
<h1>🏛️ 公考信息监控</h1>
<p class="sub">所有信息皆从公开渠道获取 <a href="rss.xml" target="_blank" style="background:#f26522;color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;text-decoration:none;margin-left:6px;vertical-align:middle">📡 RSS 订阅</a></p>
<p class="upd">最后更新：{last_update} | 每2小时自动更新</p>
</div>
<div class="stats">
<div class="st"><div class="n">{len(articles)}</div><div class="l">📋 总公告</div></div>
{source_cards}{type_cards}
</div>
<input type="text" class="srch" id="search" placeholder="🔍 搜索公告标题..." oninput="filterCards()">
<div class="fb">
<a href="#" class="on" onclick="return setF(this,'all')">全部</a>
<div class="sep"></div>
<a href="#" onclick="return setF(this,'source:国考')">🔴 国考</a>
<a href="#" onclick="return setF(this,'source:省考')">🔵 省考</a>
<a href="#" onclick="return setF(this,'source:华图')">🟢 华图</a>
<div class="sep"></div>
<a href="#" onclick="return setF(this,'type:公告')">📢 公告</a>
<a href="#" onclick="return setF(this,'type:公示')">📋 公示</a>
<a href="#" onclick="return setF(this,'type:招考')">🎯 招考</a>
<a href="#" onclick="return setF(this,'type:面试')">🎤 面试</a>
<a href="#" onclick="return setF(this,'type:职位')">💼 职位</a>
</div>
<div class="cnt" id="count"></div>
<div id="list">{cards}</div>
{pager}
<div class="ft">
<p>由 Hermes Agent 自动监控更新 · {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
</div>
</div>
<script>
function filterCards(){{const q=document.getElementById('search').value.toLowerCase();document.querySelectorAll('.card').forEach(c=>{{const t=c.querySelector('.ct').textContent.toLowerCase();c.classList.toggle('hide',q&&!t.includes(q))}})}}
function setF(el,f){{document.querySelectorAll('.fb a').forEach(b=>b.classList.remove('on'));el.classList.add('on');return false}}
</script>
</body>
</html>'''


def main():
    data = load_data()
    articles = deduplicate(data.get("announcements", []))
    last_update = data.get("last_update", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Classify
    for a in articles:
        a["type"] = classify(a.get("title", ""))
    
    total = len(articles)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    
    # Generate index.html (just page 1)
    html = index_page(articles, 1, total_pages, last_update)
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    
    # Generate articles/{hash}.html for each article
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    
    # Clean old articles
    for old in os.listdir(ARTICLES_DIR):
        if old.endswith(".html"):
            os.remove(os.path.join(ARTICLES_DIR, old))
    
    for a in articles:
        ahtml = article_page(a, articles)
        with open(os.path.join(ARTICLES_DIR, f'{a["hash"]}.html'), "w", encoding="utf-8") as f:
            f.write(ahtml)
    
    # Generate RSS feed
    rss_path = generate_rss(articles, last_update)
    
    print(f"✅ 生成完成:")
    rss_size = os.path.getsize(os.path.join(BASE_DIR, "rss.xml"))
    print(f"   rss.xml ({rss_size:,} bytes)")
    print(f"   index.html ({os.path.getsize(os.path.join(BASE_DIR, 'index.html')):,} bytes)")
    print(f"   articles/ ({len(articles)} 篇)")
    print(f"   总公告: {total}, 分页: {total_pages} 页")
    print(f"   最后更新: {last_update}")





def generate_rss(articles, last_update):
    """Generate RSS 2.0 XML feed"""
    SITE_URL = "https://heiimzy.github.io/gongkao-monitor"
    RSS_URL = SITE_URL + "/rss.xml"

    items = []
    for a in articles:
        title = xml_escape(a.get("title", ""))
        link = SITE_URL + "/articles/" + a["hash"] + ".html"
        source = xml_escape(a.get("source", ""))
        date_pub = a.get("date_pub", "")
        desc = xml_escape(a.get("content", "")[:500])

        pub_date = ""
        if date_pub:
            try:
                dt = datetime.strptime(date_pub, "%Y-%m-%d")
                pub_date = dt.strftime("%a, %d %b %Y 00:00:00 +0800")
            except Exception:
                pass

        item_lines = [
            "    <item>",
            "      <title>" + title + "</title>",
            "      <link>" + link + "</link>",
            '      <guid isPermaLink="true">' + link + "</guid>",
            "      <category>" + source + "</category>",
            "      <description>" + desc + "</description>",
        ]
        if pub_date:
            item_lines.append("      <pubDate>" + pub_date + "</pubDate>")
        item_lines.append("    </item>")
        items.append("\n".join(item_lines))

    rss_lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<rss version=\"2.0\" xmlns:atom=\"http://www.w3.org/2005/Atom\">",
        "  <channel>",
        "    <title>公考信息监控</title>",
        "    <link>" + SITE_URL + "</link>",
        "    <description>自动更新的公务员考试公告信息</description>",
        "    <language>zh-cn</language>",
        "    <lastBuildDate>" + last_update + "</lastBuildDate>",
        '    <atom:link href="' + RSS_URL + '" rel="self" type="application/rss+xml"/>',
    ]
    rss_lines.extend(items)
    rss_lines.append("  </channel>")
    rss_lines.append("</rss>")

    rss_path = os.path.join(BASE_DIR, "rss.xml")
    with open(rss_path, "w", encoding="utf-8") as f:
        f.write("\n".join(rss_lines))
    return rss_path

if __name__ == "__main__":
    main()
