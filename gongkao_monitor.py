#!/usr/bin/env python3
"""
公务员考试公告监控增强版
- 检测新公告
- 保存到 announcements.json（累积历史）
- 输出新发现的公告（供 cron job 推送）
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
    },
    {
        "name": "中公-各省省考",
        "name_short": "省考",
        "url": "https://www.offcn.com/gwy/kaoshi/",
        "keywords": ["公告", "通知", "职位", "招考", "报名", "考试", "录用", "公示", "遴选"],
    },
    {
        "name": "华图-公务员",
        "name_short": "华图",
        "url": "https://www.huatu.com/gwy/",
        "keywords": ["公告", "通知", "职位", "招考", "报名", "考试", "录用", "公示", "遴选"],
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
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
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


def url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]


def main():
    state = load_json(STATE_FILE, {})
    announcements = load_json(ANNOUNCEMENTS_FILE, {"announcements": [], "last_update": ""})
    
    # Build set of existing hashes for dedup
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
            
            # Add to announcements if not already there
            if h not in existing_hashes:
                entry = {
                    "hash": h,
                    "title": link["title"],
                    "url": link["url"],
                    "source": src["name_short"],
                    "source_full": src["name"],
                    "date_found": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "date_pub": extract_date_from_url(link["url"]),
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

    # Output new items for cron delivery
    if all_new:
        print(f"🔔 公务员公告更新 — 发现 {len(all_new)} 条新内容：\n")
        for item in all_new:
            print(f"📌 [{item['source']}] {item['title']}")
            print(f"   {item['url']}\n")


def extract_date_from_url(url):
    """Try to extract publish date from URL pattern like /2026/0624/"""
    m = re.search(r'/(\d{4})/(\d{4})/', url)
    if m:
        return f"{m.group(1)}-{m.group(2)[:2]}-{m.group(2)[2:]}"
    return ""


if __name__ == "__main__":
    main()
