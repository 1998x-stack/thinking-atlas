# Thinking Atlas · 思考图谱

**从直觉到机制，从观点到证据。** 按照 [xm-posts](https://github.com/1998x-stack/xm-posts) 的内容发布体系重构的开放研究知识库。

[阅读网站](https://1998x-stack.github.io/thinking-atlas/) · [知识地图](https://1998x-stack.github.io/thinking-atlas/topics/) · [文章归档](https://1998x-stack.github.io/thinking-atlas/archive/) · [RSS 订阅](https://1998x-stack.github.io/thinking-atlas/feed.xml)

> **证据声明**：本站包含专题分析、解释模型和待核实研究提纲。页面中的“研究提纲”不是已经完成的证据核查；原始知识记录截至 2026-09-21，重构不等于对历史论断作出了新的独立确认。不得把读者友好的图示当作统计结果或档案证据。

## 阅读方式

- **首页**：精选主题、按学科浏览、搜索索引与最新整理。
- **知识地图**：一级领域 → 二级问题 → 文章；一篇文章只有一个主分类，其他联系通过标签串联。
- **文章页**：核心问题、机制图、论证、反例与边界、证据状态和进一步研究方向。
- **文章归档**：按时间与研究状态查看全部公开内容。
- **RSS**：仅订阅内容注册表中标为 `published` 的文章。

## 内容与代码组织

```text
content/categories.json             分类与主题唯一数据源
content/posts.json                  文章元数据与研究状态
posts/<category>/<slug>/index.html  正式 HTML 阅读源文件
posts/<category>/<slug>/source.md   从旧版迁移的原始可编辑研究文本
posts/<category>/<slug>/assets/     每篇独立的原创机制图
posts/<category>/<slug>/evidence.json  来源链与核验状态
site/assets/                        全站设计系统与交互
scripts/build_site.py               生成首页、知识地图、归档、搜索、RSS、sitemap
scripts/validate_site.py            内容、路径、元数据与发布完整性检查
skills/olah-style-paper-posts/      与 xm-posts 同源的 canonical Skill
.github/workflows/publish.yml       PR 验证；main 成功后部署 Pages
_site/                              可重复生成的静态站点（禁止提交）
```

原来的 `cases/`、`domains/` 研究文本被迁移到 `posts/`，而不是直接删除其有用内容；周记、材料映射、编辑政策、研究队列归档至 `docs/`，不混入正式文章目录。

## 本地开发

要求 Python 3.11+；站点构建与基础校验仅依赖标准库。

```bash
python scripts/build_site.py
python scripts/validate_site.py
python scripts/sync_skills.py --check
python -m unittest discover -s tests -v
cd _site && python -m http.server 8000
```

在浏览器访问 http://localhost:8000/ 。GitHub Pages 使用 `/thinking-atlas/` 子路径，所有内部链接采用相对路径；站点地图和 RSS 的绝对地址由 `--base-url` 指定。

## 新增文章

1. 选择 `content/categories.json` 中的分类与主题。
2. 在 `posts/<category>/<slug>/` 创建 `index.html`、`assets/`、`evidence.json`，登记 `content/posts.json`。
3. 运用 `skills/olah-style-paper-posts/SKILL.md` 的叙事、语义 HTML、原创 SVG 和浏览器 QA 方法；历史/制度/社会研究以一手档案、政策正文、统计原表与反证检查替代论文专有章节。
4. 明确 `research_status`：`verified`、`partial`、`outline`；网站发布 `status=published` 只表示可公开阅读，不等于证据已经充分。
5. 完成构建、校验、可访问性和链接检查，经 PR 审核后合并到 `main`。不要将构建成功等同于 Pages 已部署。

详细约定见 [架构与迁移说明](docs/ARCHITECTURE.md)、[编辑与证据规范](docs/EDITORIAL.md)、[来源覆盖说明](docs/source-coverage.md)；历史来源文件及变更参见 Git 记录。

## 许可与隐私

参考 xm-posts 的信息架构与 [Olah-style-posts](https://github.com/1998x-stack/Olah-style-posts) 的教学表达方式，不复制第三方图文。图片均为项目原创的概念结构示意，不代表量化数据。公开仓库不存储私人聊天记录、私人人名或未经核实的个人传闻。