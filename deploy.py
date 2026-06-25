#!/usr/bin/env python3
"""
完整部署流程：监控 → 生成页面 → GitHub API 上传
优化版：只上传新增文章，跳过已存在的
"""
import subprocess
import requests
import base64
import json
import os
import re
import sys
from datetime import datetime
import time
import functools

# Force unbuffered output
print = functools.partial(print, flush=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GITHUB_REPO = "heiimzy/gongkao-monitor"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}"


def load_token():
    with open(os.path.expanduser("~/.config/gh/hosts.yml")) as f:
        m = re.search(r"oauth_token:\s*(.+)", f.read())
        return m.group(1).strip() if m else ""


def upload_file(token, rel_path, content, message):
    """Upload or update a file via GitHub Contents API"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.get(f"{GITHUB_API}/contents/{rel_path}", headers=headers, timeout=10)
    sha = resp.json().get("sha") if resp.status_code == 200 else None
    body = {
        "message": message,
        "content": base64.b64encode(content).decode(),
    }
    if sha:
        body["sha"] = sha
    resp = requests.put(f"{GITHUB_API}/contents/{rel_path}", headers=headers, json=body, timeout=15)
    return resp.status_code in [200, 201]


def get_github_articles(token):
    """Get list of article files already on GitHub"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.get(f"{GITHUB_API}/contents/articles", headers=headers, timeout=15)
    if resp.status_code == 200:
        return {item["name"] for item in resp.json() if item["name"].endswith(".html")}
    return set()


def main():
    # Step 1: Run monitor
    print("Step 1: Running monitor...")
    result = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "gongkao_monitor.py")],
        capture_output=True, text=True, timeout=120
    )
    monitor_output = result.stdout.strip()
    if monitor_output:
        print(monitor_output)
    else:
        print("  No new announcements")

    # Step 2: Build site
    print("\nStep 2: Building site...")
    result = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "build_site.py")],
        capture_output=True, text=True, timeout=30
    )
    print(result.stdout.strip())

    # Step 3: Upload to GitHub
    print("\nStep 3: Uploading to GitHub...")
    token = load_token()
    if not token:
        print("ERROR: No GitHub token found")
        return

    # Upload core files (always)
    core_files = ["index.html", "rss.xml", "data/announcements.json"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    ok = fail = 0

    for rel_path in core_files:
        full_path = os.path.join(BASE_DIR, rel_path)
        if not os.path.exists(full_path):
            continue
        with open(full_path, "rb") as f:
            content = f.read()
        if upload_file(token, rel_path, content, f"auto: {timestamp}"):
            ok += 1
            print(f"  OK {rel_path}")
        else:
            fail += 1
            print(f"  FAIL {rel_path}")
        time.sleep(0.3)

    # Upload articles (only new ones)
    articles_dir = os.path.join(BASE_DIR, "articles")
    if os.path.isdir(articles_dir):
        local_articles = {f for f in os.listdir(articles_dir) if f.endswith(".html")}
        github_articles = get_github_articles(token)
        new_articles = local_articles - github_articles

        if new_articles:
            print(f"  Uploading {len(new_articles)} new articles...")
            for fname in sorted(new_articles):
                full_path = os.path.join(articles_dir, fname)
                with open(full_path, "rb") as f:
                    content = f.read()
                if upload_file(token, f"articles/{fname}", content, f"new: {fname[:12]}"):
                    ok += 1
                else:
                    fail += 1
                    print(f"  FAIL articles/{fname}")
                time.sleep(0.3)
        else:
            print(f"  No new articles (all {len(local_articles)} already on GitHub)")

    print(f"\nDone: {ok} ok, {fail} fail")
    if fail == 0:
        print(f"Site updated: https://heiimzy.github.io/gongkao-monitor/")


if __name__ == "__main__":
    main()
