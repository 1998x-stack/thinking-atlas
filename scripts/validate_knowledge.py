#!/usr/bin/env python3
"""Check required knowledge pages and internal relative Markdown links."""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
issues = []
required = ["README.md", "meta/coverage.md", "meta/editorial-standard.md", "weekly/2026-09-14_2026-09-21.md"]
for name in required:
    if not (root / name).is_file():
        issues.append(f"missing required file: {name}")
mds = list(root.rglob("*.md"))
for path in mds:
    text = path.read_text(encoding="utf-8")
    for raw in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
        target = raw.split("#", 1)[0].split("?", 1)[0].strip()
        if not target or "://" in target or target.startswith(("mailto:", "#")):
            continue
        dest = (path.parent / target).resolve()
        try:
            dest.relative_to(root.resolve())
        except ValueError:
            issues.append(f"link escapes root: {path.relative_to(root)} -> {target}")
            continue
        if not dest.exists():
            issues.append(f"broken link: {path.relative_to(root)} -> {target}")
print(f"checked {len(mds)} Markdown pages; {len(issues)} issue(s)")
for issue in issues:
    print("ERROR:", issue)
sys.exit(1 if issues else 0)
