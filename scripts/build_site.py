#!/usr/bin/env python3
"""Manifest-driven static publishing for Thinking Atlas (Python 3.11+, stdlib)."""
from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "_site"
DEFAULT_BASE = "https://1998x-stack.github.io/thinking-atlas/"
LABELS = {"verified": "已核实", "partial": "部分核验", "outline": "研究提纲"}
SHORT = {"verified": "证据已核实", "partial": "需继续核验", "outline": "待研究"}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def read_manifest():
    categories = json.loads((ROOT / "content/categories.json").read_text(encoding="utf-8"))
    posts = json.loads((ROOT / "content/posts.json").read_text(encoding="utf-8"))
    return categories, posts


def text(value):
    return escape(str(value), quote=True)


def url_for(post):
    return "posts/{}/{}/".format(post["category"], post["slug"])


def nav_item(prefix, path, label, active):
    current = ' aria-current="page"' if active == label else ""
    return '<a href="{}{}"{}>{}</a>'.format(prefix, path, current, label)


def shell(title, desc, body, depth=0, active="", base_url=DEFAULT_BASE, path=""):
    prefix = "../" * depth
    canonical = base_url.rstrip("/") + "/" + path
    header = "".join([
        nav_item(prefix, "", "首页", active),
        nav_item(prefix, "topics/", "知识地图", active),
        nav_item(prefix, "archive/", "文章归档", active),
        nav_item(prefix, "methodology/", "研究方法", active),
    ])
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>{text(title)} · Thinking Atlas</title>
<meta name="description" content="{text(desc)}">
<link rel="canonical" href="{text(canonical)}">
<link rel="alternate" type="application/rss+xml" title="Thinking Atlas RSS" href="{prefix}feed.xml">
<link rel="icon" type="image/svg+xml" href="{prefix}assets/favicon.svg">
<link rel="stylesheet" href="{prefix}assets/site.css">
<script defer src="{prefix}assets/site.js"></script>
</head>
<body>
<a class="skip-link" href="#main">跳至正文</a>
<header class="site-header"><div class="container header-row">
<a class="wordmark" href="{prefix}" aria-label="Thinking Atlas 首页">thinking<span>atlas</span><span class="wordmark-dot">.</span></a>
<nav class="top-nav" aria-label="主导航">{header}</nav>
</div></header>
{body}
<footer class="site-footer"><div class="container footer-inner">
<div><strong>Thinking Atlas</strong><p>从直觉到机制，从观点到证据。</p></div>
<div class="footer-links"><a href="{prefix}topics/">领域导航</a><a href="{prefix}archive/">全部文章</a><a href="{prefix}feed.xml">RSS</a><a href="https://github.com/1998x-stack/thinking-atlas">GitHub 源码</a></div>
<p class="footer-note">概念模型不代表已验证的因果结论。公开内容可能仍处于研究提纲阶段。</p>
</div></footer>
</body></html>'''


def card(post, prefix="", compact=False):
    href = prefix + url_for(post)
    cover = href + post["cover"]["src"]
    status = LABELS[post["research_status"]]
    tags = ", ".join(post.get("tags", []))
    cls = "post-card compact-card" if compact else "post-card"
    return f'''<article class="{cls}" data-search="{text(post["title"] + " " + post["summary"] + " " + tags)}" data-domain="{text(post["category"])}" data-status="{text(post["research_status"])}">
<a class="cover-link" href="{href}" tabindex="-1" aria-hidden="true"><img loading="lazy" decoding="async" src="{cover}" alt=""></a>
<div class="card-content">
<div class="card-meta"><span class="status-tag status-{text(post["research_status"])}">{status}</span><span>{post["reading_minutes"]} 分钟阅读</span></div>
<h3><a href="{href}">{text(post["title"])}</a></h3>
<p>{text(post["summary"])}</p>
<div class="card-foot"><span>{text(post["updated"])}</span><a href="{href}" aria-label="阅读：{text(post["title"])}">阅读文章 <span aria-hidden="true">↗</span></a></div>
</div></article>'''


def category_block(cat, posts, prefix=""):
    ps = [p for p in posts if p["category"] == cat["slug"]]
    sample = "".join(card(p, prefix, compact=True) for p in ps[:2])
    return f'''<section class="category-block" aria-label="{text(cat["title"])}">
<div class="category-heading"><span class="eyebrow">{text(cat.get("english", ""))}</span><h3><a href="{prefix}categories/{cat["slug"]}/">{text(cat["title"])}</a></h3><p>{text(cat["description"])}</p></div>
<div class="category-preview">{sample}</div><a class="text-link" href="{prefix}categories/{cat["slug"]}/">进入领域 · 共 {len(ps)} 篇</a></section>'''


def build_home(categories, posts, base_url):
    posts = sorted(posts, key=lambda x: (x["updated"], x["slug"]), reverse=True)
    counts = Counter(p["research_status"] for p in posts)
    featured = posts[:6]
    field_options = "".join(f'<option value="{text(c["slug"])}">{text(c["title"])}</option>' for c in categories)
    all_cards = "".join(card(p) for p in posts)
    lines = "".join(
        f'<a class="path-item" href="categories/{c["slug"]}/"><span class="path-number">{i:02d}</span><span><b>{text(c["title"])}</b><small>{text(c["description"])}</small></span><span class="path-arrow">↗</span></a>'
        for i, c in enumerate(categories, 1))
    body = f'''<main id="main">
<section class="hero container">
<div class="hero-copy"><div class="eyebrow"><span class="eyebrow-dot"></span> A FIELD GUIDE TO BETTER QUESTIONS</div>
<h1>从直觉到机制，<br><em>从观点到证据。</em></h1>
<p class="hero-lede">思考图谱不是观点陈列室，而是一套可查来源、可质疑、可修订的研究地图。我们用图解打开复杂问题，用材料与反例约束答案。</p>
<div class="hero-actions"><a class="button button-primary" href="topics/">探索知识地图 <span aria-hidden="true">↗</span></a><a class="button button-secondary" href="archive/">浏览全部文章</a></div>
<div class="hero-stats"><div><strong>{len(posts)}</strong><span>开放主题</span></div><div><strong>{len(categories)}</strong><span>研究领域</span></div><div><strong>{counts["outline"]}</strong><span>待核实提纲</span></div></div>
</div>
<div class="hero-visual" role="img" aria-label="研究方法：从问题到证据，经机制与反证检验，不断形成更可靠的有限结论">
<div class="visual-tag">THE RESEARCH LOOP <span>01 / 04</span></div>
<div class="orbit-center">为什么<br>会这样？</div>
<div class="orbit-node orbit-a"><b>01</b><span>明确问题</span></div><div class="orbit-node orbit-b"><b>02</b><span>寻找证据</span></div><div class="orbit-node orbit-c"><b>03</b><span>检验机制</span></div><div class="orbit-node orbit-d"><b>04</b><span>寻找反例</span></div>
<div class="visual-caption">结论始终有边界。每次新增证据，都可以修订已有判断。</div>
</div></section>
<section class="section-band"><div class="container"><div class="section-intro"><div><span class="eyebrow">SELECTED READING</span><h2>打开一条思考路径</h2><p>从具体制度、历史事件和真实选择切入，看到它们背后的变量。</p></div><a class="text-link" href="archive/">阅读全部文章 ↗</a></div>
<div class="post-grid">{"".join(card(p) for p in featured)}</div></div></section>
<section class="container section-pad"><div class="section-intro"><div><span class="eyebrow">KNOWLEDGE MAP</span><h2>把问题放回所属领域</h2><p>每篇文章只有一个主归属，用跨领域标签连接，而不制造重复结论。</p></div><a class="text-link" href="topics/">完整知识地图 ↗</a></div>
<div class="paths-grid">{lines}</div></section>
<section class="index-section"><div class="container">
<div class="section-intro"><div><span class="eyebrow">ALL NOTES</span><h2>文章索引</h2><p>按关键词、研究领域及核验状态查找；研究提纲不会被当作已核实的结论。</p></div></div>
<form class="search-bar" role="search" onsubmit="return false"><label class="sr-only" for="search">搜索文章</label><input id="search" type="search" placeholder="搜索主题、机制、标签…" autocomplete="off"><label class="sr-only" for="domain">领域</label><select id="domain"><option value="">全部领域</option>{field_options}</select><label class="sr-only" for="research-status">核验状态</label><select id="research-status"><option value="">全部状态</option><option value="partial">部分核验</option><option value="outline">研究提纲</option><option value="verified">已核实</option></select></form>
<div class="filter-summary" id="result-count" aria-live="polite">共 {len(posts)} 篇文章</div><div class="post-grid" id="post-index">{all_cards}</div>
<p id="no-results" class="empty-message" hidden>没有匹配的条目。请尝试其他关键词或移除筛选。</p>
</div></section>
<section class="container research-note"><div><span class="eyebrow">A NOTE ON EVIDENCE</span><h2>先标明不知道什么，<br>才能继续找到答案。</h2></div>
<div><p>本库部分研究始于有限聊天索引或既有笔记，不等于逐项完成原始文献核查。页面会分别提示“部分核验”与“研究提纲”。概念机制图用于解释变量，不代表统计估计。</p><a class="text-link" href="methodology/">阅读证据与出版原则 ↗</a></div></section></main>'''
    return shell("研究型知识图谱", "从直觉到机制，从观点到证据。制度、历史、经济、技术与研究方法的可追溯研究索引。", body, active="首页", base_url=base_url)


def build_topics(categories, posts, base_url):
    groups = []
    for c in categories:
        topics = "".join(
            f'<li><a href="../categories/{c["slug"]}/#topic-{t["slug"]}">{text(t["title"])}</a></li>'
            for t in c["topics"]
        )
        count = sum(p["category"] == c["slug"] for p in posts)
        groups.append(f'<section class="topic-panel"><span class="eyebrow">{text(c.get("english", ""))}</span><h2><a href="../categories/{c["slug"]}/">{text(c["title"])}</a></h2><p>{text(c["description"])}</p><ul>{topics}</ul><div class="topic-count">{count} 篇公开研究</div></section>')
    body = '<main id="main" class="container section-pad"><div class="page-heading"><span class="eyebrow">KNOWLEDGE MAP</span><h1>知识地图</h1><p>一级研究领域 → 二级问题 → 可独立阅读的文章。跨领域联系通过标签与原文链接建立。</p></div><div class="topics-grid">' + "".join(groups) + '</div></main>'
    return shell("知识地图", "按领域与主题探索 Thinking Atlas", body, depth=1, active="知识地图", base_url=base_url, path="topics/")


def build_category(cat, posts, base_url):
    here = [p for p in posts if p["category"] == cat["slug"]]
    groups = []
    for t in cat["topics"]:
        items = [p for p in here if p["topic"] == t["slug"]]
        groups.append(f'<section class="topic-section" id="topic-{t["slug"]}"><div class="section-intro"><div><span class="eyebrow">RESEARCH TOPIC</span><h2>{text(t["title"])}</h2></div><span class="count-pill">{len(items)} 篇</span></div><div class="post-grid">{"".join(card(p,"../../") for p in items)}</div></section>')
    body = f'<main class="container section-pad" id="main"><nav class="breadcrumb" aria-label="当前位置"><a href="../../topics/">知识地图</a> / <span>{text(cat["title"])}</span></nav><div class="page-heading"><span class="eyebrow">{text(cat.get("english", ""))}</span><h1>{text(cat["title"])}</h1><p>{text(cat["description"])}</p></div>{"".join(groups)}</main>'
    return shell(cat["title"], cat["description"], body, depth=2, active="知识地图", base_url=base_url, path=f'categories/{cat["slug"]}/')


def build_archive(posts, page, size, base_url):
    ordered = sorted(posts, key=lambda p: (p["updated"], p["slug"]), reverse=True)
    start = (page - 1) * size
    group = ordered[start:start + size]
    pages = (len(posts) + size - 1) // size
    prefix = "../" if page == 1 else "../../../"
    pager_links = []
    for i in range(1, pages + 1):
        attr = ' aria-current="page"' if i == page else ""
        href = prefix + "archive/" + (f"page/{i}/" if i > 1 else "")
        pager_links.append(f'<a{attr} href="{href}">{i}</a>')
    pages_html = "".join(pager_links)
    body = f'<main class="container section-pad" id="main"><div class="page-heading"><span class="eyebrow">COMPLETE ARCHIVE</span><h1>文章归档</h1><p>共 {len(posts)} 篇公开文章；“已发布”不意味着研究结论已得到实证证实。</p></div><div class="archive-header">按最近修订排序 · 第 {page}/{pages} 页</div><div class="post-grid">{"".join(card(p,prefix) for p in group)}</div><nav class="pager" aria-label="归档分页">{pages_html}</nav></main>'
    path = "archive/" if page == 1 else f"archive/page/{page}/"
    return shell("文章归档", "完整的公开研究文章归档", body, depth=1 if page == 1 else 3, active="文章归档", base_url=base_url, path=path)


def build_methodology(base_url):
    body = '''<main class="container section-pad" id="main">
<div class="page-heading"><span class="eyebrow">EDITORIAL PRINCIPLES</span><h1>研究方法与证据边界</h1><p>以有限、可核对的论断替代笼统判断；以持续反证替代陈列观点。</p></div>
<div class="method-grid">
<section><span class="method-no">01</span><h2>问题先于结论</h2><p>从一个可检验问题开始，限定时间、地区、制度版本与概念定义，不把个人直觉当作事实。</p></section>
<section><span class="method-no">02</span><h2>事实、推论与假设分开</h2><p>重要主张必须注明原始资料与适用范围；机制图只呈现分析结构，不表达样本或因果识别结果。</p></section>
<section><span class="method-no">03</span><h2>独立核验与反证</h2><p>优先原始法条、司法裁判、史书原文、统计资料与研究报告；比较反证与不同解释。</p></section>
<section><span class="method-no">04</span><h2>诚实记录未知</h2><p>研究提纲就是提纲，材料汇编不是独立验证。每篇文章记录证据状态与后续可执行研究任务。</p></section>
</div><section class="method-callout"><h2>关于本文库原始资料</h2><p>初始整理于 2026-09-21，使用当时可见的部分提问及六份既有文本；并未取得账户级完整聊天资料，原文本的写作日期也未被证明。新版站点的发布与页面重排不构成对全部具体历史、政策或统计论断的再核验。</p><a href="https://github.com/1998x-stack/thinking-atlas/tree/main/docs">查看来源覆盖与编辑规范 ↗</a></section></main>'''
    return shell("研究方法", "事实与推论的分离、原始证据、反证与研究提纲状态的说明", body, depth=1, active="研究方法", base_url=base_url, path="methodology/")


def build_feed(posts, base_url):
    base = base_url.rstrip("/") + "/"
    items = []
    for p in sorted(posts, key=lambda x: (x["updated"], x["slug"]), reverse=True):
        link = base + url_for(p)
        date = datetime.strptime(p["published"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        items.append(f'''<item><title>{xml_escape(p["title"])}</title><link>{xml_escape(link)}</link><guid isPermaLink="true">{xml_escape(link)}</guid><description>{xml_escape(p["summary"])}</description><category>{xml_escape(p["category"])}</category><pubDate>{format_datetime(date, usegmt=True)}</pubDate><dcterms:modified>{p["updated"]}</dcterms:modified></item>''')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dcterms="http://purl.org/dc/terms/">
<channel><title>Thinking Atlas · 思考图谱</title><link>{xml_escape(base)}</link><description>从直觉到机制，从观点到证据。</description><language>zh-CN</language><atom:link href="{xml_escape(base+"feed.xml")}" rel="self" type="application/rss+xml"/>{''.join(items)}</channel></rss>'''


def build_sitemap(categories, posts, base_url, pages):
    base = base_url.rstrip("/") + "/"
    paths = ["", "topics/", "archive/", "methodology/"]
    paths += [f"archive/page/{i}/" for i in range(2, pages + 1)]
    paths += [f"categories/{c['slug']}/" for c in categories]
    paths += [url_for(p) for p in posts]
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{xml_escape(base+x)}</loc></url>' for x in paths) + '</urlset>'


def save(relative, content):
    output = DEST / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")


def publish(base_url, archive_size=16):
    categories, posts = read_manifest()
    public = [p for p in posts if p["status"] == "published"]
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir()
    shutil.copytree(ROOT / "site/assets", DEST / "assets")
    for p in public:
        src = ROOT / url_for(p)
        dst = DEST / url_for(p)
        dst.mkdir(parents=True)
        shutil.copy2(src / "index.html", dst / "index.html")
        if (src / "assets").is_dir():
            shutil.copytree(src / "assets", dst / "assets")
    save("index.html", build_home(categories, public, base_url))
    save("topics/index.html", build_topics(categories, public, base_url))
    for c in categories:
        save(f'categories/{c["slug"]}/index.html', build_category(c, public, base_url))
    pages = max(1, (len(public) + archive_size - 1) // archive_size)
    for page in range(1, pages + 1):
        path = "archive/index.html" if page == 1 else f"archive/page/{page}/index.html"
        save(path, build_archive(public, page, archive_size, base_url))
    save("methodology/index.html", build_methodology(base_url))
    save("feed.xml", build_feed(public, base_url))
    save("sitemap.xml", build_sitemap(categories, public, base_url, pages))
    save("posts.json", json.dumps([
        {key: p[key] for key in ("slug", "title", "category", "topic", "research_status", "updated", "summary", "tags")}
        for p in public], ensure_ascii=False, indent=2))
    base_path = "./"
    save("robots.txt", "User-agent: *\nAllow: /\nSitemap: " + base_url.rstrip("/") + "/sitemap.xml\n")
    save("404.html", shell("页面未找到", "您访问的页面不存在", '<main id="main" class="container section-pad"><div class="page-heading"><h1>没有找到这个页面</h1><p>文章可能迁移或地址有误。</p><a class="button button-primary" href="' + base_path + '">返回首页</a></div></main>', base_url=base_url))
    print(f"BUILD OK: {len(public)} articles, {len(categories)} categories, {pages} archive page(s) -> {DEST}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--archive-size", type=int, default=16)
    args = parser.parse_args()
    if not args.base_url.startswith(("https://", "http://")):
        parser.error("base URL must use HTTP(S)")
    if args.archive_size < 1:
        parser.error("archive-size must be positive")
    publish(args.base_url, args.archive_size)


if __name__ == "__main__":
    main()
