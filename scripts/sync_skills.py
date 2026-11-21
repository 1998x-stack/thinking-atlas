#!/usr/bin/env python3
"""Keep four self-contained agent skill directories identical to canonical source."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'skills/olah-style-paper-posts'
MIRRORS=[ROOT/d/'skills/olah-style-paper-posts' for d in ('.claude','.pi','.agent','.opencode')]


def content_map(path:Path):
    return {str(f.relative_to(path)):f.read_bytes() for f in path.rglob('*') if f.is_file() and '__pycache__' not in f.parts and not f.name.endswith('.pyc')}


def run(check:bool=False):
    source=content_map(SOURCE)
    assert 'SKILL.md' in source and len(source)>=14
    for target in MIRRORS:
        if check:
            other=content_map(target) if target.is_dir() else {}
            if other!=source:
                missing=set(source)-set(other);extra=set(other)-set(source)
                bad=[f for f in source.keys()&other.keys() if source[f]!=other[f]]
                raise SystemExit(f'Skill mirror out of sync: {target}: missing={missing}, extra={extra}, changed={bad}')
            print('OK',target.relative_to(ROOT),len(source),'files')
        else:
            if target.exists():shutil.rmtree(target)
            shutil.copytree(SOURCE,target,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            print('SYNC',target.relative_to(ROOT))

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');a=ap.parse_args();run(a.check)
