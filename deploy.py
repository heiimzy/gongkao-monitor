#!/usr/bin/env python3
"""
完整部署流程：监控 → 生成页面 → GitHub API 上传
国内服务器 git push 超时，改用 REST API
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

    # Check if file exists
    resp = requests.get(f"{GITHUB_API}/contents/{rel_path}", headers=headers)
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    body = {
        "message": message,
        "content": base64.b64encode(content).decode(),
    }
    if sha:
        body["sha"] = sha

    resp = requests.put(f"{GITHUB_API}/contents/{rel_path}", headers=headers, json=body)
    return resp.status_code in [200, 201]


def main():
    # Step 1: Run monitor
    print("📡 Step 1: 运行公告监控...")
    result = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "gongkao_monitor.py")],
        capture_output=True, text=True, timeout=120
    )
    monitor_output = result.stdout.strip()
    has_new = bool(monitor_output)
    if monitor_output:
        print(monitor_output)

    # Step 2: Build site
    print("\n🔨 Step 2: 生成页面...")
    result = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "build_site.py")],
        capture_output=True, text=True, timeout=30
    )
    print(result.stdout.strip())

    # Step 3: Upload to GitHub
    print("\n🚀 Step 3: 上传到 GitHub Pages...")
    token = load_token()
    if not token:
        print("❌ No GitHub token found")
        return

    files_to_upload = [
        "index.html",
        "rss.xml",
        "README.md",
        "gongkao_monitor.py",
        "build_site.py",
        "deploy.py",
        "data/announcements.json",
    ]

    # Also upload all article pages
    articles_dir = os.path.join(BASE_DIR, "articles")
    if os.path.isdir(articles_dir):
        for fname in sorted(os.listdir(articles_dir)):
            if fname.endswith(".html"):
                files_to_upload.append(f"articles/{fname}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    all_ok = True

    for rel_path in files_to_upload:
        full_path = os.path.join(BASE_DIR, rel_path)
        if not os.path.exists(full_path):
            continue
        with open(full_path, "rb") as f:
            content = f.read()
        ok = upload_file(token, rel_path, content, f"auto-update: {timestamp}")
        status = "✅" if ok else "❌"
        print(f"  {status} {rel_path}")
        if not ok:
            all_ok = False
        time.sleep(0.3)  # Rate limit friendly

    if all_ok:
        print(f"\n✅ 公考页面已更新")
        print(f"🔗 https://heiimzy.github.io/gongkao-monitor/")
    else:
        print("\n⚠️ 部分文件上传失败")


if __name__ == "__main__":
    main()
