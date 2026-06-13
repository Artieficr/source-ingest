#!/usr/bin/env python3
"""
semantic-search.py

Usage:
  python3 semantic-search.py "query" [top_n] [--threshold 0.6]   — search wiki
  python3 semantic-search.py --rebuild [--threshold 0.6]          — rebuild full index
  python3 semantic-search.py --update "page1,page2"               — add pages to index
"""

import sys
import json
import math
import os
import re
import urllib.request

WIKI_DIR = "Wiki"
INDEX_FILE = "Scripts/wiki-index.json"
OLLAMA_URL = os.environ.get("OLLAMA_EMBEDDINGS_URL", "http://localhost:11434/api/embeddings")
EMBED_MODEL = "bge-m3"
DEFAULT_THRESHOLD = 0.6
EXCLUDE = {"log", "index"}


def get_embedding(text):
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["embedding"]


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r") as f:
            return json.load(f)
    return {}


def save_index(index):
    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f)


def extract_text(content):
    """Strip frontmatter before embedding, so frontmatter fields (including
    the related/conflicts link lists) don't influence the page's vector."""
    body = re.sub(r'^---\n.*?\n---\n?', '', content, flags=re.DOTALL)
    return body.strip()


def index_page(filename, index):
    path = os.path.join(WIKI_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return False
    if len(content.strip()) < 50:
        return False
    name = filename.replace(".md", "")
    print(f"  Indexing: {name}", file=sys.stderr)
    vec = get_embedding(extract_text(content)[:2000])
    index[name] = vec
    return True


def rebuild():
    print("Rebuilding wiki index...", file=sys.stderr)
    index = {}
    if not os.path.exists(WIKI_DIR):
        print(f"Wiki directory not found: {WIKI_DIR}", file=sys.stderr)
        sys.exit(1)
    pages = [f for f in os.listdir(WIKI_DIR) if f.endswith('.md') and f not in {'index.md', 'log.md'}]
    for page in pages:
        index_page(page, index)
    save_index(index)
    print(f"Done. Indexed {len(index)} pages.", file=sys.stderr)


def update(pages_csv):
    index = load_index()
    pages = [p.strip() for p in pages_csv.split(",") if p.strip()]
    for page in pages:
        filename = page if page.endswith(".md") else page + ".md"
        index_page(filename, index)
    save_index(index)
    print(f"Updated {len(pages)} pages.", file=sys.stderr)


def search(query, top_n=5, threshold=DEFAULT_THRESHOLD):
    index = load_index()
    if not index:
        print("[]")
        return
    query_vec = get_embedding(query)
    scores = []
    for name, vec in index.items():
        if name.lower() in EXCLUDE:
            continue
        score = cosine_similarity(query_vec, vec)
        if score >= threshold:
            scores.append((name, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    results = [name for name, _ in scores[:top_n]]
    print(json.dumps(results))


def parse_args(args):
    threshold = DEFAULT_THRESHOLD
    filtered = []
    i = 0
    while i < len(args):
        if args[i] == '--threshold' and i + 1 < len(args):
            threshold = float(args[i + 1])
            i += 2
        else:
            filtered.append(args[i])
            i += 1
    return filtered, threshold


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: semantic-search.py <query> [top_n] [--threshold 0.6] | --rebuild | --update <pages>")
        sys.exit(1)

    args, threshold = parse_args(args)

    if args[0] == "--rebuild":
        rebuild()
    elif args[0] == "--update":
        if len(args) < 2:
            print("--update requires comma-separated page names")
            sys.exit(1)
        update(args[1])
    else:
        if args[-1].isdigit():
            top_n = int(args[-1])
            query = ' '.join(args[:-1])
        else:
            top_n = 5
            query = ' '.join(args)
        search(query, top_n, threshold)
