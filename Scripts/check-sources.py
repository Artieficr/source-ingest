#!/usr/bin/env python3
"""
check-sources.py

Usage:
  python3 check-sources.py scan                    — list all unprocessed sources
  python3 check-sources.py check "<path>"          — check if specific source is safe to ingest
  python3 check-sources.py mark "<path>"           — mark source as processed
  python3 check-sources.py unmark "<path>"         — mark source as unprocessed
"""

import sys
import os
import re
import json

SOURCES_ROOT = "Sources"


def parse_frontmatter(content):
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, _, value = line.partition(':')
            fm[key.strip()] = value.strip().strip('"\'')
    return fm


def set_processed(content, value):
    if re.search(r'^processed:', content, re.MULTILINE):
        return re.sub(r'^processed:.*$', f'processed: {value}', content, flags=re.MULTILINE)
    return re.sub(r'^(---\n[\s\S]*?)\n---', rf'\1\nprocessed: {value}\n---', content, count=1)


def scan():
    results = []
    for root, dirs, files in os.walk(SOURCES_ROOT):
        dirs[:] = [d for d in dirs if d != 'space']
        for f in files:
            if f.endswith('.md'):
                path = os.path.join(root, f).replace('\\', '/')
                try:
                    with open(path, 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    fm = parse_frontmatter(content)
                    if fm.get('processed', '').lower() != 'true':
                        title = fm.get('title', f.replace('.md', ''))
                        results.append({'path': path, 'title': title})
                except Exception:
                    pass
    print(json.dumps(results, indent=2))


def check(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        fm = parse_frontmatter(content)
        processed = fm.get('processed', '').lower() == 'true'
        title = fm.get('title', os.path.basename(path).replace('.md', ''))
        print(json.dumps({'path': path, 'title': title, 'processed': processed, 'safe_to_ingest': not processed}, indent=2))
    except FileNotFoundError:
        print(json.dumps({'path': path, 'error': 'File not found', 'safe_to_ingest': False}))


def mark(path, value):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        updated = set_processed(content, value)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(updated)
        action = 'marked' if value == 'true' else 'unmarked'
        print(json.dumps({'path': path, action: True}))
    except Exception as e:
        print(json.dumps({'path': path, 'error': str(e)}))


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print("Usage: check-sources.py scan | check <path> | mark <path> | unmark <path>")
        sys.exit(1)

    action = args[0]
    if action == 'scan':
        scan()
    elif action == 'check':
        if len(args) < 2:
            print("check requires a path")
            sys.exit(1)
        check(args[1])
    elif action == 'mark':
        if len(args) < 2:
            print("mark requires a path")
            sys.exit(1)
        mark(args[1], 'true')
    elif action == 'unmark':
        if len(args) < 2:
            print("unmark requires a path")
            sys.exit(1)
        mark(args[1], 'false')
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
