#!/usr/bin/env python3
"""Validate manifest integrity, source bundles and generated Pages site."""
from __future__ import annotations

import json
import posixpath
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"_site"
SLUG=re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STATUSES={"published","draft"}
RESEARCH={"verified","partial","outline"}


class InspectHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links=[]
        self.ids=set()
        self.headings=[]
        self.main=0
        self.article=0
        self.images=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag in {"a","link"} and a.get("href"):
            self.links.append((tag,"href",a["href"]))
        if tag in {"script","img"} and a.get("src"):
            self.links.append((tag,"src",a["src"]))
        if tag=="img":
            self.images.append(a)
        if tag=="h1":
            self.headings.append(tag)
        if tag=="main":
            self.main+=1
        if tag=="article":
            self.article+=1


def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))


def assert_true(condition,message,errors):
    if not condition:
        errors.append(message)


def validate_sources():
    errors=[]
    cats=load("content/categories.json")
    posts=load("content/posts.json")
    cs=set()
    topics={}
    for c in cats:
        s=c.get("slug","")
        assert_true(bool(SLUG.fullmatch(s)),f"invalid category slug: {s}",errors)
        assert_true(s not in cs,f"duplicate category: {s}",errors)
        cs.add(s)
        tset=set()
        assert_true(bool(c.get("topics")),f"category has no topics: {s}",errors)
        for t in c.get("topics",[]):
            ts=t.get("slug","")
            assert_true(bool(SLUG.fullmatch(ts)),f"invalid topic slug: {s}/{ts}",errors)
            assert_true(ts not in tset,f"duplicate topic: {s}/{ts}",errors)
            tset.add(ts)
        topics[s]=tset
    slugs=set()
    for p in posts:
        slug=p.get("slug","")
        cat=p.get("category","")
        source=ROOT/"posts"/cat/slug
        assert_true(bool(SLUG.fullmatch(slug)),f"invalid slug: {slug}",errors)
        assert_true(slug not in slugs,f"duplicate post slug: {slug}",errors)
        slugs.add(slug)
        assert_true(p.get("status") in STATUSES,f"invalid publish status: {slug}",errors)
        assert_true(p.get("research_status") in RESEARCH,f"invalid research state: {slug}",errors)
        assert_true(cat in cs,f"unknown category: {slug}",errors)
        assert_true(p.get("topic") in topics.get(cat,set()),f"unknown topic: {slug}",errors)
        for day in ("published","updated"):
            assert_true(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}",p.get(day,""))),f"missing ISO date: {slug}/{day}",errors)
        for key in ("title","summary","subtitle"):
            assert_true(bool(p.get(key)),f"missing metadata: {slug}/{key}",errors)
        assert_true(isinstance(p.get("reading_minutes"),int) and p["reading_minutes"]>0,f"invalid reading time: {slug}",errors)
        assert_true((source/"source.md").is_file(),f"missing source.md: {slug}",errors)
        assert_true((source/"index.html").is_file(),f"missing index.html: {slug}",errors)
        evidence=source/"evidence.json"
        assert_true(evidence.is_file(),f"missing evidence: {slug}",errors)
        if evidence.exists():
            ev=json.loads(evidence.read_text(encoding="utf-8"))
            assert_true(ev.get("research_status")==p.get("research_status"),f"evidence status mismatch: {slug}",errors)
            assert_true(bool(ev.get("source",{}).get("original_path")),f"missing provenance: {slug}",errors)
            assert_true(ev.get("independent_recheck")!="complete" or bool(ev.get("verified_claims")),f"unsubstantiated recheck claim: {slug}",errors)
        image=source/p.get("cover",{}).get("src","missing")
        assert_true(image.is_file(),f"missing article cover: {slug}",errors)
        if image.is_file():
            svg=image.read_text(encoding="utf-8")
            assert_true('viewBox=' in svg and "<title" in svg and "<desc" in svg,f"SVG lacks accessibility metadata: {slug}",errors)
            try:
                ET.fromstring(svg)
            except ET.ParseError as ex:
                errors.append(f"invalid SVG {slug}: {ex}")
        html=(source/"index.html")
        if html.exists():
            parser=InspectHTML()
            parser.feed(html.read_text(encoding="utf-8"))
            assert_true(parser.main==1 and parser.article==1,f"article structure: {slug}",errors)
            assert_true(len(parser.headings)==1,f"must have one H1: {slug}",errors)
            assert_true(any("文章" in x or "核验" in x for x in [html.read_text(encoding="utf-8")]),f"missing research disclosure: {slug}",errors)
    return cats,posts,errors


def local_target(source,raw):
    url=urlsplit(raw)
    if url.scheme or url.netloc or raw.startswith(("mailto:","tel:","data:","javascript:")):
        return None,None
    if url.path.startswith("/"):
        # Hard-coded absolute links are inappropriate on a GitHub project site.
        return "ABSOLUTE",raw
    target=source.parent/unquote(url.path)
    if not url.path or url.path.endswith("/"):
        target=target/"index.html"
    elif target.suffix=="":
        target=target/"index.html"
    return target.resolve(),url.fragment


def validate_built(posts,cats):
    errors=[]
    if not SITE.is_dir():
        return ["_site missing: first run python scripts/build_site.py"]
    required={"index.html","topics/index.html","archive/index.html","methodology/index.html","posts.json","feed.xml","sitemap.xml","robots.txt","404.html"}
    required.update(f"categories/{c['slug']}/index.html" for c in cats)
    required.update(f"posts/{p['category']}/{p['slug']}/index.html" for p in posts if p['status']=="published")
    for rel in required:
        assert_true((SITE/rel).is_file(),f"missing output: {rel}",errors)
    seen=0
    for html in SITE.rglob("*.html"):
        inspect=InspectHTML()
        try:
            inspect.feed(html.read_text(encoding="utf-8"))
        except Exception as ex:
            errors.append(f"malformed HTML parser input: {html}: {ex}")
            continue
        assert_true(inspect.main==1,f"page must have one main: {html.relative_to(SITE)}",errors)
        assert_true(len(inspect.headings)==1,f"page must have one H1: {html.relative_to(SITE)}",errors)
        for tag,attr,href in inspect.links:
            target,frag=local_target(html,href)
            if target is None:
                continue
            if target=="ABSOLUTE":
                errors.append(f"project-site absolute link: {html.relative_to(SITE)} -> {frag}")
                continue
            if not target.is_relative_to(SITE.resolve()):
                errors.append(f"link escapes output root: {html.relative_to(SITE)} -> {href}")
            elif not target.is_file():
                errors.append(f"broken link: {html.relative_to(SITE)} -> {href}")
            elif frag and target.suffix.lower()==".html":
                actual=InspectHTML()
                actual.feed(target.read_text(encoding="utf-8"))
                if unquote(frag) not in actual.ids:
                    errors.append(f"broken fragment: {html.relative_to(SITE)} -> {href}")
        for img in inspect.images:
            assert_true("alt" in img,f"image missing alt: {html.relative_to(SITE)}",errors)
        seen+=1
    bad=[str(p.relative_to(SITE)) for p in SITE.rglob("*") if p.is_file() and (p.suffix in {".md",".py"} or p.name=="evidence.json")]
    assert_true(not bad,f"private sources leaked into output: {bad}",errors)
    try:
        rss=ET.parse(SITE/"feed.xml").getroot()
        items=rss.findall("./channel/item")
        n=sum(p["status"]=="published" for p in posts)
        assert_true(len(items)==n,f"RSS items mismatch {len(items)} vs {n}",errors)
        guids=[i.findtext("guid") for i in items]
        assert_true(len(guids)==len(set(guids)),"duplicate RSS GUIDs",errors)
        ET.parse(SITE/"sitemap.xml")
    except Exception as ex:
        errors.append(f"invalid RSS/sitemap XML: {ex}")
    try:
        public=json.loads((SITE/"posts.json").read_text(encoding="utf-8"))
        assert_true(len(public)==sum(p["status"]=="published" for p in posts),"public search index count mismatch",errors)
    except Exception as ex:
        errors.append(f"invalid public search JSON: {ex}")
    print(f"LINK CHECK: scanned {seen} HTML pages")
    return errors


def main():
    cats,posts,errors=validate_sources()
    errors+=validate_built(posts,cats)
    if errors:
        for issue in errors:
            print("FAIL:",issue,file=sys.stderr)
        raise SystemExit(f"VALIDATION FAILED: {len(errors)} finding(s)")
    print(f"VALIDATION OK: {len(posts)} posts; {len(cats)} categories; source, links, SVG, RSS and sitemap verified")


if __name__=="__main__":
    main()
