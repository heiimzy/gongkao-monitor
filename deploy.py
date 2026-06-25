#!/usr/bin/env python3
"""
完整的部署流程：监控 → 生成页面 → git push
由 cron job 调用
"""
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd, check=True):
    result = subprocess.run(
        cmd, shell=True, cwd=BASE_DIR,
        capture_output=True, text=True, timeout=60
    )
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}", file=sys.stderr)
        print(f"   stderr: {result.stderr}", file=sys.stderr)
        return False
    return result


def main():
    # Step 1: Run monitor
    print("📡 Step 1: 运行公告监控...")
    result = run(f"python3 {os.path.join(BASE_DIR, 'gongkao_monitor.py')}")
    if result is False:
        return
    
    monitor_output = result.stdout.strip()
    has_new = bool(monitor_output)
    if monitor_output:
        print(monitor_output)

    # Step 2: Build site
    print("\n🔨 Step 2: 生成页面...")
    result = run(f"python3 {os.path.join(BASE_DIR, 'build_site.py')}")
    if result is False:
        return
    print(result.stdout.strip())

    # Step 3: Git commit and push
    print("\n🚀 Step 3: 推送到 GitHub...")
    
    # Check if there are changes
    status = run("git status --porcelain", check=False)
    if status and status.stdout.strip():
        run("git add -A")
        run('git commit -m "auto-update: ' + (__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')) + '"')
        push = run("git push origin main")
        if push is False:
            print("⚠️ Push failed, trying to set upstream...")
            run("git push -u origin main")
        else:
            print("✅ 已推送到 GitHub Pages")
    else:
        print("ℹ️ 没有变化，跳过推送")

    # Output for cron delivery
    if has_new:
        print(f"\n📢 公考页面已更新，访问: https://heiimzy.github.io/gongkao-monitor/")


if __name__ == "__main__":
    main()
