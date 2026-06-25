#!/usr/bin/env python3
"""清理 announcements.json 中的垃圾内容"""
import json, re, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANN_FILE = os.path.join(BASE_DIR, "data", "announcements.json")

# 垃圾内容模式
JUNK_PATTERNS = [
    r'中公教育【全流程领航计划】',
    r'公务员考试笔试都考什么内容',
    r'各省公务员考试公告一般在哪里查看',
    r'公务员考试申论应该如何积累素材',
    r'行测考试都考什么，计算题难不难',
    r'资料分析题有没有快速作答的方法',
    r'公务员考试面试的考试流程什么样',
    r'公务员考试什么时候查询成绩',
    r'各省公务员考综合试成绩计算方法',
    r'公务员考试面试形式有哪些',
    r'各省公务员考试面试时间安排',
    r'公务员考试笔试都考什么内容',
    r'<a href.*?target.*?>(.*?)</a>',
    r'加微信.*',
    r'点我咨询.*',
    r'咨询客服.*',
    r'声明：.*',
    r'还在为考编.*',
    r'收藏此页.*',
    r'有报考疑惑.*',
    r'点击问题咨询.*',
    r'公务员考试信息\.\.\.',
    r'国家公务员考试\.\.\.',
    r'公务员考试培训课程\.\.\.',
    r'公务员考试真题\.\.\.',
    r'公务员考试时间\.\.\.',
    r'公务员考试资料\.\.\.',
    r'公务员考试问答\.\.\.',
    r'国家公务员职位表\.\.\.',
    r'国家公务员考试录用系统\.\.\.',
    r'国家公务员考试公告\.\.\.',
    r'国家公务员考试大纲\.\.\.',
    r'国家公务员考试专业分类目录\.\.\.',
    r'国家公务员考试报名入口\.\.\.',
    r'国家公务员考试报考条件\.\.\.',
    r'国家公务员考试费用\.\.\.',
    r'国家公务员考试报名人数\.\.\.',
    r'国家公务员考试准考证打印入口\.\.\.',
    r'国家公务员考试成绩查询入口\.\.\.',
    r'国家公务员考试分数线\.\.\.',
    r'国家公务员面试公告\.\.\.',
    r'国家公务员考试体检标准\.\.\.',
    r'国家公务员考试录用公示\.\.\.',
    r'[a-zA-Z]+人事考试信息\.\.\.',
    r'[a-zA-Z]+公务员考试\.\.\.',
    r'￥\d+.*',
    r'公务员考试.*?￥\d+',
    r'<a href="[^"]*"[^>]*>.*?</a>',
]

# 标题级别的垃圾（整条删掉）
TITLE_JUNK = [
    r'^公务员考试信息$',
    r'^国家公务员考试$',
    r'^公务员考试培训课程$',
    r'^公务员考试真题$',
    r'^公务员考试时间$',
    r'^公务员考试资料$',
    r'^公务员考试问答$',
    r'^国家公务员职位表$',
    r'^国家公务员考试录用系统$',
    r'^国家公务员考试公告$',
    r'^国家公务员考试大纲$',
    r'^国家公务员考试专业分类目录$',
    r'^国家公务员考试报名入口$',
    r'^国家公务员考试报考条件$',
    r'^国家公务员考试费用$',
    r'^国家公务员考试报名人数$',
    r'^国家公务员考试准考证打印入口$',
    r'^国家公务员考试成绩查询入口$',
    r'^国家公务员考试分数线$',
    r'^国家公务员面试公告$',
    r'^国家公务员考试体检标准$',
    r'^国家公务员考试录用公示$',
    r'^[a-zA-Z]+人事考试信息$',
    r'^[a-zA-Z]+公务员考试$',
    r'^职位查询\s*报岗系统$',
    r'^省考招录职位表$',
    r'^地方公务员考试信息$',
    r'^2023北京事业单位公告',
    r'^2020京考公告',
    r'^京考职位表下载',
    r'^公务员考试.*?￥',
    r'^.*?book.*?￥',
    r'^同等学力申硕考试$',
]


def clean_content(text):
    """清理文章正文中的垃圾"""
    if not text:
        return ""
    
    lines = text.split("\n")
    cleaned = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip junk patterns
        skip = False
        for pat in JUNK_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                skip = True
                break
        if skip:
            continue
        
        # Skip very short lines (likely nav fragments)
        if len(line) < 8:
            continue
        
        # Skip lines that are just dates repeated
        if re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$', line):
            if cleaned:  # Skip duplicate date lines (keep first)
                continue
        
        cleaned.append(line)
    
    # Remove trailing junk (sometimes the last few lines are all junk)
    while cleaned and len(cleaned[-1]) < 15:
        cleaned.pop()
    
    return "\n".join(cleaned)


def is_junk_title(title):
    """检查标题是否是垃圾"""
    title = title.strip()
    for pat in TITLE_JUNK:
        if re.match(pat, title):
            return True
    return False


def main():
    with open(ANN_FILE) as f:
        data = json.load(f)
    
    before = len(data["announcements"])
    
    # Filter out junk titles
    data["announcements"] = [
        a for a in data["announcements"]
        if not is_junk_title(a.get("title", ""))
    ]
    
    # Clean content
    for a in data["announcements"]:
        if a.get("content"):
            a["content"] = clean_content(a["content"])
    
    # Filter out articles with no meaningful content after cleaning
    data["announcements"] = [
        a for a in data["announcements"]
        if a.get("content") and len(a["content"]) > 80
    ]
    
    after = len(data["announcements"])
    
    # Sort by date
    data["announcements"].sort(key=lambda x: x.get("date_found", ""), reverse=True)
    data["total"] = len(data["announcements"])
    
    with open(ANN_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"清理完成: {before} → {after} 条 (删除了 {before - after} 条垃圾)")
    
    # Show stats
    sources = {}
    for a in data["announcements"]:
        s = a.get("source", "?")
        sources[s] = sources.get(s, 0) + 1
    for s, c in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")


if __name__ == "__main__":
    main()
