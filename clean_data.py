#!/usr/bin/env python3
"""全面清理数据 + 内容去噪"""
import json, re, os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANN_FILE = os.path.join(BASE_DIR, "data", "announcements.json")
CUTOFF = "2026-05"

TITLE_JUNK = [
    r'^公务员考试信息', r'^国家公务员考试$', r'^公务员考试培训', r'^公务员考试真题',
    r'^公务员考试时间$', r'^公务员考试资料', r'^公务员考试问答', r'^国家公务员职位表$',
    r'^国家公务员考试录用系统', r'^国家公务员考试公告$', r'^国家公务员考试大纲',
    r'^国家公务员考试专业分类', r'^国家公务员考试报名入口', r'^国家公务员考试报考条件',
    r'^国家公务员考试费用', r'^国家公务员考试报名人数', r'^国家公务员考试准考证',
    r'^国家公务员考试成绩查询', r'^国家公务员考试分数线', r'^国家公务员面试公告',
    r'^国家公务员考试体检', r'^国家公务员考试录用公示', r'^[a-zA-Z]+人事考试信息',
    r'^[a-zA-Z]+公务员考试$', r'^职位查询\s*报岗系统$', r'^省考招录职位表$',
    r'^地方公务员考试信息', r'^2023北京事业单位', r'^2020京考', r'^京考职位表',
    r'^同等学力申硕', r'^公务员考试.*?￥', r'^.*?book.*?￥',
    r'^20\d{2}(?:下半年|上半年)?公务员考试申论.*?解析', r'^20\d{2}多省.*?申论.*?解读',
    r'^面试技巧.*?(?:面试官|如何答|应急处突|人际类|计划组织)', r'^面试热点',
    r'^公务员考试面试模拟题', r'^广东省考面试题库', r'^2025广东公务员面试试题',
    r'^2024广东公务员面试试题', r'^面试每日一练', r'^面试试题',
    r'^公务员面试.*?模拟题',
]

CONTENT_JUNK = [
    r'中公教育【全流程领航计划】', r'公务员考试笔试都考什么内容',
    r'各省公务员考试公告一般在哪里查看', r'公务员考试申论应该如何积累素材',
    r'行测考试都考什么，计算题难不难', r'资料分析题有没有快速作答的方法',
    r'公务员考试面试的考试流程什么样', r'公务员考试什么时候查询成绩',
    r'各省公务员考综合试成绩计算方法', r'公务员考试面试形式有哪些',
    r'各省公务员考试面试时间安排', r'加微信.*', r'点我咨询.*', r'咨询客服.*',
    r'声明：.*', r'还在为考编.*', r'收藏此页.*', r'有报考疑惑.*',
    r'点击问题咨询.*', r'公务员考试信息\.\.\.', r'国家公务员考试\.\.\.',
    r'公务员考试培训课程\.\.\.', r'公务员考试真题\.\.\.', r'公务员考试时间\.\.\.',
    r'公务员考试资料\.\.\.', r'公务员考试问答\.\.\.', r'国家公务员职位表\.\.\.',
    r'国家公务员考试录用系统\.\.\.', r'国家公务员考试公告\.\.\.',
    r'国家公务员考试大纲\.\.\.', r'国家公务员考试报名入口\.\.\.',
    r'国家公务员考试报考条件\.\.\.', r'国家公务员考试费用\.\.\.',
    r'国家公务员考试报名人数\.\.\.', r'国家公务员考试准考证打印入口\.\.\.',
    r'国家公务员考试成绩查询入口\.\.\.', r'国家公务员考试分数线\.\.\.',
    r'国家公务员面试公告\.\.\.', r'国家公务员考试体检标准\.\.\.',
    r'国家公务员考试录用公示\.\.\.', r'[a-zA-Z]+人事考试信息\.\.\.',
    r'[a-zA-Z]+公务员考试\.\.\.', r'公务员考试.*?￥\d+', r'￥\d+.*',
    r'<a href[^>]*>.*?</a>',
    r'^山东公务员考试(?!.*公示|.*公告.*发布)', r'^山东公务员考试一年考几次',
    r'^.*?山东省考职位都有哪些', r'^山东公务员考试报名条件$',
    r'^山东公务员考试报名入口在哪', r'^山东公务员考试历年信息',
    r'^1\.\d+-\d+日?报名',
]


def fix_excel(text):
    def rep(m):
        try: return str(int(float(m.group(0))))
        except: return m.group(0)
    return re.sub(r'\d+\.\d+E\+\d+', rep, text)


def clean_content(text):
    if not text: return ""
    text = fix_excel(text)
    cleaned = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) < 6: continue
        if any(re.search(p, line, re.I) for p in CONTENT_JUNK): continue
        if re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$', line) and cleaned: continue
        if line.startswith("原标题：") or line.startswith("文章来源："): continue
        cleaned.append(line)
    while cleaned and len(cleaned[-1]) < 20: cleaned.pop()
    return "\n".join(cleaned)


def is_junk_title(title):
    return any(re.match(p, title.strip()) for p in TITLE_JUNK)


def main():
    with open(ANN_FILE) as f: data = json.load(f)
    before = len(data["announcements"])
    
    data["announcements"] = [a for a in data["announcements"]
        if a.get("date_pub","").startswith(CUTOFF) or a.get("date_found","").startswith(CUTOFF)]
    after_date = len(data["announcements"])
    
    data["announcements"] = [a for a in data["announcements"]
        if not is_junk_title(a.get("title",""))]
    after_title = len(data["announcements"])
    
    for a in data["announcements"]:
        if a.get("content"): a["content"] = clean_content(a["content"])
    
    data["announcements"] = [a for a in data["announcements"]
        if a.get("content") and len(a["content"]) > 60]
    after_clean = len(data["announcements"])
    
    data["announcements"].sort(key=lambda x: x.get("date_pub","") or x.get("date_found",""), reverse=True)
    data["total"] = len(data["announcements"])
    data["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(ANN_FILE, "w") as f: json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"清理完成: {before} → {after_date}(日期) → {after_title}(标题) → {after_clean}(最终)")
    sources = {}
    for a in data["announcements"]: sources[a.get("source","?")] = sources.get(a.get("source","?"),0)+1
    for s,c in sorted(sources.items(), key=lambda x:-x[1]): print(f"  {s}: {c}")


if __name__ == "__main__": main()
