#!/usr/bin/env python3
"""Fast concurrent upload to GitHub Pages"""
import requests, base64, json, os, re, time, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

with open(os.path.expanduser("~/.config/gh/hosts.yml")) as f:
    content = f.read()
    m = re.search(r'oauth_token:\s*(.+)', content)
    token = m.group(1).strip()

H = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
API = "https://api.github.com/repos/heiimzy/gongkao-monitor"
PROJECT = "/home/admin/gongkao-monitor"

def upload_one(rel, filepath):
    for attempt in range(3):
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            resp = requests.get(f"{API}/contents/{rel}", headers=H, timeout=10)
            sha = resp.json().get("sha") if resp.status_code == 200 else None
            body = {
                "message": f"update: {os.path.basename(rel)}",
                "content": base64.b64encode(data).decode()
            }
            if sha:
                body["sha"] = sha
            r = requests.put(f"{API}/contents/{rel}", headers=H, json=body, timeout=15)
            if r.status_code in [200, 201]:
                return (rel, True, "")
            if r.status_code == 403 and "rate limit" in r.text.lower():
                time.sleep(30)
                continue
            if r.status_code == 422:
                return (rel, True, "unchanged")
            return (rel, False, f"HTTP {r.status_code}")
        except Exception as e:
            time.sleep(2)
    return (rel, False, "max retries")

files = []
for name in ["index.html", "rss.xml", "build_site.py", "upload.py", "deploy.py"]:
    p = os.path.join(PROJECT, name)
    if os.path.exists(p):
        files.append((name, p))

articles_dir = os.path.join(PROJECT, "articles")
for fname in sorted(os.listdir(articles_dir)):
    if fname.endswith(".html"):
        files.append((f"articles/{fname}", os.path.join(articles_dir, fname)))

print(f"Uploading {len(files)} files...")
ok = fail = 0
start = time.time()

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(upload_one, rel, path): rel for rel, path in files}
    for i, future in enumerate(as_completed(futures)):
        rel, success, msg = future.result()
        if success:
            ok += 1
        else:
            fail += 1
            print(f"  FAIL {rel}: {msg}")
        if (i + 1) % 20 == 0:
            elapsed = time.time() - start
            print(f"  [{i+1}/{len(files)}] ok={ok} fail={fail} ({elapsed:.0f}s)")

elapsed = time.time() - start
print(f"Done: {ok} ok, {fail} fail ({elapsed:.0f}s)")
