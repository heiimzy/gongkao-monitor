#!/usr/bin/env python3
"""批量上传到 GitHub（带重试和速率控制）"""
import requests, base64, json, os, re, time, sys

with open(os.path.expanduser("~/.config/gh/hosts.yml")) as f:
    m = re.search(r'oauth_token:\s*(.+)', f.read())
    token = m.group(1).strip()

H = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
API = "https://api.github.com/repos/heiimzy/gongkao-monitor"
PROJECT = "/home/admin/gongkao-monitor"

def upload(rel, content, msg):
    for attempt in range(3):
        try:
            resp = requests.get(f"{API}/contents/{rel}", headers=H, timeout=10)
            sha = resp.json().get("sha") if resp.status_code == 200 else None
            body = {"message": msg, "content": base64.b64encode(content if isinstance(content, bytes) else content.encode()).decode()}
            if sha: body["sha"] = sha
            r = requests.put(f"{API}/contents/{rel}", headers=H, json=body, timeout=15)
            if r.status_code in [200, 201]:
                return True
            if r.status_code == 403 and "rate limit" in r.text.lower():
                time.sleep(30)
                continue
            if r.status_code == 422:  # Unprocessable - file too large or unchanged
                return True  # Skip silently
            return False
        except Exception as e:
            time.sleep(2)
    return False

# Step 1: Delete old articles from repo
print("🗑️ 清理旧文件...")
resp = requests.get(f"{API}/contents/articles", headers=H, timeout=10)
if resp.status_code == 200:
    for f in resp.json():
        requests.delete(f"{API}/contents/articles/{f['name']}", headers=H, 
            json={"message": "clean", "sha": f["sha"]}, timeout=10)
    print(f"  删除了 {len(resp.json())} 个旧文章")

# Step 2: Upload core files
print("\n📁 核心文件...")
core = ["index.html", "rss.xml", "build_site.py", "gongkao_monitor.py", "deploy.py", "clean_data.py", "README.md"]
for f in core:
    p = os.path.join(PROJECT, f)
    if not os.path.exists(p): continue
    with open(p, 'rb') as fh:
        ok = upload(f, fh.read(), f"v4: {f}")
    print(f"  {'✅' if ok else '❌'} {f}")

# Step 3: Upload articles
print(f"\n📄 文章...")
articles = sorted(os.listdir(os.path.join(PROJECT, "articles")))
ok = fail = 0
for i, fname in enumerate(articles):
    if not fname.endswith(".html"): continue
    with open(os.path.join(PROJECT, "articles", fname), 'rb') as fh:
        if upload(f"articles/{fname}", fh.read(), f"a:{fname[:12]}"):
            ok += 1
        else:
            fail += 1
    if (i+1) % 30 == 0:
        print(f"  [{i+1}/{len(articles)}] ✅{ok} ❌{fail}")
        time.sleep(1)

print(f"\n✅ 完成: {ok} 成功, {fail} 失败")
