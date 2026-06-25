#!/usr/bin/env python3
"""
公务员考试公告监控增强版 v2
- 检测新公告
- 抓取文章正文（华图完整内容，中公摘要）
- 保存到 announcements.json
"""
import requests
import hashlib
import json
import os
import sys
import re
from datetime import datetime
from urllib.parse import urljoin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ANNOUNCEMENTS_FILE = os.path.join(DATA_DIR, "announcements.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")

SOURCES = [
    {
        "name": "中公-国考",
        "name_short": "国考",
        "url": "https://www.offcn.com/gwy/",
        "keywords": ["公告", "通知", "职位", "招考", "报名", "考试", "录用", "公示", "笔试", "面试", "体检", "遴选"],
        "type": "offcn",
    },
    {
        "name": "中公-各省省考",
        "name_short": "省考",
        "url": "https://www.offcn.com/gwy/kaoshi/",
        "keywords": ["公告", "通知", "职位", "招考", "报名", "考试", "录用", "公示", "遴选"],
        "type": "offcn",
    },
    {
        "name": "华图-公务员",
        "name_short": "华图",
        "url": "https://www.huatu.com/gwy/",
        "keywords": ["公告", "通知", "职位", "招考", "报名", "考试", "录用", "公示", "遴选"],
        "type": "huatu",
    },
]


def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch(url, timeout=15):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=timeout)
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except Exception as e:
        print(f"  ⚠️ {url}: {e}", file=sys.stderr)
        return None


def extract_links(html, base_url):
    links = []
    for m in re.finditer(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL):
        href, txt = m.group(1), re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if txt and len(txt) > 6:
            full_url = urljoin(base_url, href) if href.startswith("/") else href
            links.append({"url": full_url, "title": txt.replace("\r", "").replace("\n", " ")})
    return links


def extract_content_offcn(html):
    """Extract content from offcn (中公) article page"""
    # Find title
    h1_m = re.search(r'<h1[^>]*class="zg_Htitle"[^>]*>(.*?)</h1>', html, re.DOTALL)
    title = ""
    if h1_m:
        title = re.sub(r'<[^>]+>', '', h1_m.group(1)).strip()
    
    # Find content between h1 and footer
    start = h1_m.end() if h1_m else 0
    footer_pos = html.find('class="footer"', start)
    if footer_pos < 0:
        footer_pos = start + 15000
    
    section = html[start:footer_pos]
    
    # Remove non-content elements
    section = re.sub(r'<script[^>]*>.*?</script>', '', section, flags=re.DOTALL)
    section = re.sub(r'<style[^>]*>.*?</style>', '', section, flags=re.DOTALL)
    section = re.sub(r'<div[^>]*class="[^"]*(?:ydms|咨询|客服|lxwm|hotNews)[^"]*"[^>]*>.*?</div>', '', section, flags=re.DOTALL)
    
    text = re.sub(r'<[^>]+>', '\n', section)
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 10]
    
    # Filter out navigation/ad content
    skip_patterns = ['咨询', '客服', '点击问题', '加微信', '收藏此页', '声明：', '还在为考编']
    content_lines = [l for l in lines if not any(p in l[:30] for p in skip_patterns)]
    
    return {
        "title": title,
        "content": "\n".join(content_lines[:15]),
        "source_type": "offcn",
    }


def extract_content_huatu(html):
    """Extract content from Huatu (华图) article page"""
    # Find title
    h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    title = re.sub(r'<[^>]+>', '', h1_m.group(1)).strip() if h1_m else ""
    
    # Find content in artBcon div
    content_m = re.search(r'<div class="artBcon">(.*?)</div>\s*(?:</div>|<div class)', html, re.DOTALL)
    if not content_m:
        # Try broader pattern
        content_m = re.search(r'class="artBcon"[^>]*>(.*?)(?:<div class="(?:tab-r|footer|copyright))', html, re.DOTALL)
    
    content = ""
    if content_m:
        raw = content_m.group(1)
        raw = re.sub(r'<script[^>]*>.*?</script>', '', raw, flags=re.DOTALL)
        raw = re.sub(r'<br\s*/?>', '\n', raw)
        raw = re.sub(r'<[^>]+>', ' ', raw)
        raw = re.sub(r'\s+', ' ', raw).strip()
        # Split into lines for readability
        raw = re.sub(r'([。！？])', r'\1\n', raw)
        content = "\n".join(l.strip() for l in raw.split('\n') if l.strip() and len(l.strip()) > 5)
    
    if not content:
        # Fallback: extract paragraphs
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
        paragraphs = [re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs]
        paragraphs = [p for p in paragraphs if len(p) > 30 and '咨询' not in p[:20] and '客服' not in p[:20]]
        content = "\n".join(paragraphs[:15])
    
    return {
        "title": title,
        "content": content,
        "source_type": "huatu",
    }


def scrape_article(url, source_type):
    """Scrape article content based on source type"""
    html = fetch(url)
    if not html:
        return ""
    
    if source_type == "huatu":
        result = extract_content_huatu(html)
    else:
        result = extract_content_offcn(html)
    
    return result.get("content", "")


def url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]


def extract_date_from_url(url):
    m = re.search(r'/(\d{4})/(\d{4})/', url)
    if m:
        return f"{m.group(1)}-{m.group(2)[:2]}-{m.group(2)[2:]}"
    return ""


def main():
    state = load_json(STATE_FILE, {})
    announcements = load_json(ANNOUNCEMENTS_FILE, {"announcements": [], "last_update": ""})
    
    existing_hashes = {a["hash"] for a in announcements["announcements"]}
    all_new = []

    for src in SOURCES:
        key = src["name"]
        if key not in state:
            state[key] = {"known": [], "last": ""}

        html = fetch(src["url"])
        if not html:
            continue

        links = extract_links(html, src["url"])
        known_set = set(state[key]["known"])

        for link in links:
            if not any(kw in link["title"] for kw in src["keywords"]):
                continue
            h = url_hash(link["url"])
            if h not in known_set:
                state[key]["known"].append(h)
            
            if h not in existing_hashes:
                # Scrape article content
                print(f"  📥 抓取内容: {link['title'][:50]}...", file=sys.stderr)
                content = scrape_article(link["url"], src["type"])
                
                entry = {
                    "hash": h,
                    "title": link["title"],
                    "url": link["url"],
                    "source": src["name_short"],
                    "source_full": src["name"],
                    "date_found": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "date_pub": extract_date_from_url(link["url"]),
                    "content": content[:3000],  # Limit content size
                }
                announcements["announcements"].append(entry)
                existing_hashes.add(h)
                all_new.append(entry)

        state[key]["last"] = datetime.now().isoformat()

    # Sort by date_found descending
    announcements["announcements"].sort(key=lambda x: x["date_found"], reverse=True)
    announcements["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    announcements["total"] = len(announcements["announcements"])

    save_json(STATE_FILE, state)
    save_json(ANNOUNCEMENTS_FILE, announcements)

    if all_new:
        print(f"🔔 公务员公告更新 — 发现 {len(all_new)} 条新内容：\n")
        for item in all_new:
            print(f"📌 [{item['source']}] {item['title']}")
            print(f"   {item['url']}\n")


if __name__ == "__main__":
    main()
