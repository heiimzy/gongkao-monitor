# 公考信息监控 🏛️

自动追踪中公教育、华图教育等平台的公务员考试公告。

## 功能

- 🔍 **自动监控** — 每2小时自动抓取最新公告
- 📊 **数据聚合** — 按来源（国考/省考/华图）分类整理
- 🔎 **搜索过滤** — 支持关键词搜索和来源筛选
- 📱 **响应式设计** — 手机/电脑均可正常浏览

## 数据来源

- [中公教育 - 国考](https://www.offcn.com/gwy/)
- [中公教育 - 省考](https://www.offcn.com/gwy/kaoshi/)
- [华图教育 - 公务员](https://www.huatu.com/gwy/)

## 技术栈

- 纯静态 HTML/CSS/JS（无依赖）
- Python 脚本自动抓取和生成
- GitHub Pages 托管

## 自动更新

由 Hermes Agent 定时任务驱动，每2小时：
1. 运行 `gongkao_monitor.py` 抓取新公告
2. 运行 `build_site.py` 重新生成页面
3. `git push` 到 GitHub Pages

---

*Powered by Hermes Agent*
