# Thinking Atlas · Agent 协作契约

## 任务定位
以 `xm-posts` 的清单驱动静态出版架构、`olah-style-paper-posts` 的渐进式解释框架重塑研究型知识库。所有修改必须保留可追溯的原始知识内容，避免把研究提纲误称完成研究。

## 不可破坏的契约
1. `content/categories.json` 是领域/主题单一事实源，`content/posts.json` 是文章单一事实源。
2. 一篇文章只有一个稳定 `category` 和 `topic`；采用 `posts/<category>/<slug>/index.html`。
3. `status=published` 表示页面可公开阅读；`research_status` 独立表示 `verified|partial|outline`，不许混淆。
4. 核心事实附权威来源、原始 URL 和具体范围；未核实的原记录按原样注明核验限制。
5. 每篇文章有独立的 SVG 机制图（自带 title/desc）及 `evidence.json`；不得伪造统计图、因果推论或核验完成状态。
6. 不得发布私人原始聊天、隐私材料、错误的人物传记推测或大段未经许可复制的材料。
7. `_site/` 为生成物，只由 CI 部署，不入库。部署前必须跑 `build_site.py`、`validate_site.py`、Skill 同步检查与测试。
8. 修改 canonical Skill 后运行 `python scripts/sync_skills.py`；其他代理目录只是镜像。
9. 删除旧路径须先将有用内容迁入 `posts/` 或 `docs/`，并修复任何引用；重构只能在独立分支，经 PR 检查。

## 文章制作门禁
以 [olah-style-paper-posts](skills/olah-style-paper-posts/SKILL.md) 为设计与 QA 基准，但不把 ML 论文的张量/公式格式机械套到法史社科研究。此类文章改用“研究问题 → 已核实材料 → 候选机制 → 竞争解释 → 反证与局限 → 下一步证据”框架。所有示例、图示与分类为解释辅助，不能假装已取得实证。

## 验收
校验 100% 注册项的源 HTML / SVG / evidence 文件存在；内部链接无断链；RSS 和 sitemap 仅含公开文章；同一 slug 不重复；移动端不横向滚动，键盘导航与可访问名称有效。未实际测试的项目必须标记为未验证。