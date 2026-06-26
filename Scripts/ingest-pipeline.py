#!/usr/bin/env python3
"""
ingest-pipeline.py — modular /ingest pipeline driven step-by-step by an
agentic model (any model — this script makes no model calls of its own).

Each subcommand does a small, bounded piece of work and then tells the
calling model exactly what to do next and which command to run. The model
should treat every invocation as a fresh, self-contained step: read this
command's output, do what it says, run the next command. Progress is kept in
Scripts/.ingest-state.json so an interrupted run can be resumed by re-running
'start "<source path>"'.

Commands:
  start ["<source path>"] - begin (or resume) an ingest; prints instructions
                            for retelling the source (the model reads the
                            source text itself -- this command does not print
                            it). If no path is given, resumes the in-progress
                            ingest if any, otherwise picks the next unprocessed source
                            automatically (via check-sources.py scan). To
                            ingest everything, just keep re-running
                            'start' with no path after each "Ingest
                            complete." until it reports nothing left.
  concepts                - (stdin) the concept-grouped retelling; creates
                            one page per concept.
  link no|related|conflict - judges the relationship between the current page
                            and the candidate found via semantic search,
                            after reading both pages in full.
  status                  - show current progress.
  abandon                 - cancel the in-progress ingest, removing any
                            draft/partial pages it created, so a new ingest
                            can be started.
"""

import sys
import os
import re
import json
import subprocess
import importlib
from datetime import datetime

WIKI_DIR = "Wiki"
TEMPLATE_PATH = "Schema/Templates/wiki-page-template.md"
INDEX_PATH = "Wiki/_meta/index.md"
LOG_PATH = "Wiki/_meta/log.md"
STATE_FILE = "Scripts/.ingest-state.json"

CATEGORIES = ["technique", "tool", "background", "typology", "effect", "other"]

SEARCH_TOP_N = 15

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
SEARCH_THRESHOLD = importlib.import_module("semantic-search").DEFAULT_THRESHOLD


# ---------------------------------------------------------------------------
# Instructions shown to the calling model at each step

RETELL_INSTRUCTIONS = """Start your reply with a line "QUOTE: <sentence>", where <sentence> is \
a real sentence (20+ characters) copied verbatim from the source file -- this proves you've \
read it. Submissions without a verbatim quote from the source are rejected.

Then retell the source as prose, broken into self-contained concepts \
and grouped by idea (not by where they happen to fall in the source).

This applies even if the source is already a well-structured article. Don't \
just copy its existing headings -- re-group at a finer grain. A source with 3 \
top-level headings might still become 8-10 concept blocks if it actually \
covers that many distinct ideas; the source's existing structure is not the \
target structure.

For each concept, write a block in this exact format:

## Concept: <short, specific title>
Category: <technique|tool|background|typology|effect|other>

<the finished wiki-page text for this concept -- see rules below>

Repeat for every concept worth its own wiki page. Guidelines:
- Categories: technique (a named method/procedure), tool (a named \
product/API/specific entity), background (a person, project, historical \
event, etymology), typology (a categorized list of named types/styles), \
effect (a named effect/phenomenon/concept), other (anything else substantial).
- Group by concept, not by position -- if the source returns to the same \
idea twice, merge both mentions into one concept block.
- Skip ads/sponsor segments, intros/outros, and pure filler -- don't give \
them concept blocks.
- Use only information that is actually in the source. Don't add outside \
knowledge, and don't omit specific details, numbers, or named examples that \
are present.
- Each concept should be substantial enough to stand alone (a paragraph or \
more of source material) -- don't create a block for a passing one-line \
mention.

The body of each concept block is the finished wiki page -- write it \
accordingly:
- Retell everything the source says about this concept, in your own words, \
grouped together even if the source mentions it in several separate places.
- Remove filler, rhetorical questions, conversational asides, \
meta-commentary (e.g. "as I said earlier", "let's get into it", "now the big \
question is"), and repetition.
- Write in clear, direct prose paragraphs. No headings, no timestamps, no \
bullet lists unless the content is inherently a list of named items.
- Roughly 100-800 words."""

LINK_INSTRUCTIONS = """Read both pages in full and judge their relationship:

- "no" -- the pages aren't actually about the same concept (a semantic search \
match that doesn't hold up on a full read). No link is recorded.
- "related" -- they cover the same or overlapping concept and a reader of one \
would benefit from knowing about the other, but they don't contradict each \
other. Both pages get linked via their "related" frontmatter list.
- "conflict" -- on top of being related, they state contradicting facts, \
numbers, claims, or recommendations about the same specific point. Both pages \
get linked via both their "related" and "conflicts" frontmatter lists.

If unsure between "related" and "conflict", choose "related"."""


# ---------------------------------------------------------------------------
# Generic helpers

def fail(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    return text


def parse_frontmatter(content):
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).split('\n'):
        if ':' in line and not line.startswith(' '):
            key, _, value = line.partition(':')
            fm[key.strip()] = value.strip().strip('"\'')
    return fm


def normalize_for_match(text):
    text = re.sub(r'[*_`]', '', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text



def replace_section(content, heading, new_body):
    pattern = re.compile(rf'^{re.escape(heading)}\n(.*?)(\n*)(?=^## |\Z)', re.MULTILINE | re.DOTALL)
    m = pattern.search(content)
    if not m:
        return content.rstrip('\n') + f'\n\n{heading}\n{new_body}\n'
    sep = '\n' if m.end() >= len(content) else '\n\n'
    return content[:m.start(1)] + new_body + sep + content[m.end():]


# ---------------------------------------------------------------------------
# Concept blocks (written by the calling model to stdin of 'concepts')

CONCEPT_BLOCK_RE = re.compile(
    r'^## Concept: ([^\n]+)\nCategory: ([^\n]+)\n+(.*?)(?=^## Concept: |\Z)',
    re.MULTILINE | re.DOTALL,
)


def parse_concepts_text(text):
    concepts = []
    for m in CONCEPT_BLOCK_RE.finditer(text):
        title = m.group(1).strip()
        category = m.group(2).strip().lower()
        if category not in CATEGORIES:
            category = "other"
        body = m.group(3).strip()
        if title and body:
            concepts.append({"title": title, "category": category, "content": body})
    return concepts


# ---------------------------------------------------------------------------
# Pages

def resolve_filename(title, source_link):
    """Returns (slug, is_duplicate). is_duplicate=True means a page for this
    exact concept from this exact source already exists (idempotent rerun)."""
    base_slug = slugify(title)
    candidate = base_slug
    n = 2
    while True:
        path = os.path.join(WIKI_DIR, f"{candidate}.md")
        if not os.path.exists(path):
            return candidate, False
        with open(path, encoding="utf-8") as f:
            existing_fm = parse_frontmatter(f.read())
        if existing_fm.get("source", "") == f"[[{source_link}]]":
            return candidate, True
        candidate = f"{base_slug}--{n}"
        n += 1


def render_page(template, title, category, source_link, body):
    out = template
    out = out.replace('{{TITLE}}', title.replace('"', "'"))
    out = out.replace('{{CATEGORY}}', category)
    out = out.replace('{{SOURCE_NAME}}', source_link)
    out = out.replace('{{CREATED_DATE}}', datetime.now().strftime('%Y-%m-%d'))
    out = out.replace('{{BODY}}', body)
    return out


def read_page_content(slug):
    path = os.path.join(WIKI_DIR, f"{slug}.md")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    fm = parse_frontmatter(content)
    title = fm.get("title", slug)
    m = re.search(r'^## Content\n(.*?)(?=\n## |\Z)', content, re.MULTILINE | re.DOTALL)
    body = m.group(1).strip() if m else ""
    return {"title": title, "body": body}


def append_frontmatter_list(page_path, field, slug):
    """Mechanically append one Obsidian wikilink to a frontmatter list field,
    if not already present. Empty fields use flow style ('related: []');
    non-empty fields use YAML block style ('related:\\n  - "[[a]]"')."""
    if not os.path.exists(page_path):
        return False
    with open(page_path, encoding="utf-8") as f:
        content = f.read()

    entry = f'"[[{slug}]]"'

    # Block-style list: "field:\n  - ...\n  - ..."
    block_pattern = re.compile(rf'^{re.escape(field)}:[ \t]*\n((?:^[ \t]+- .*\n)*)', re.MULTILINE)
    m = block_pattern.search(content)
    if m:
        items_block = m.group(1)
        items = re.findall(r'^[ \t]+-\s*(.*)$', items_block, re.MULTILINE)
        if entry in items:
            return True
        new_block = items_block + f'  - {entry}\n'
        content = content[:m.start(1)] + new_block + content[m.end(1):]
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    # Flow-style list: "field: [...]"
    flow_pattern = re.compile(rf'^{re.escape(field)}: \[(.*?)\]$', re.MULTILINE)
    m = flow_pattern.search(content)
    if not m:
        return False

    items_str = m.group(1).strip()
    items = [i.strip() for i in items_str.split(',') if i.strip()] if items_str else []
    if entry in items:
        return True
    items.append(entry)

    new_block = f"{field}:\n" + "".join(f"  - {i}\n" for i in items)
    content = content[:m.start()] + new_block.rstrip('\n') + content[m.end():]
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def semantic_search(query, top_n=SEARCH_TOP_N, threshold=SEARCH_THRESHOLD):
    result = subprocess.run(
        [sys.executable, "Scripts/semantic-search.py", query, str(top_n), "--threshold", str(threshold)],
        capture_output=True, text=True,
    )
    try:
        return json.loads(result.stdout.strip())
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Finalization

def append_to_index(page_names):
    content = "# Wiki Index\n"
    existing = set()
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, encoding="utf-8") as f:
            content = f.read()
        existing = set(m.lower() for m in re.findall(r'\[\[([^\]]+)\]\]', content))

    new_entries = [f'- [[{p}]]' for p in page_names if p.lower() not in existing]
    if new_entries:
        sep = '' if content.endswith('\n') else '\n'
        os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            f.write(content + sep + '\n'.join(new_entries) + '\n')


def compute_updated_pages(related_links, conflict_links):
    updated = []
    for link in related_links + conflict_links:
        existing_page = link.split(' <-> ')[1]
        if existing_page not in updated:
            updated.append(existing_page)
    return updated


def append_to_log(source_name, created, related_links, conflict_links):
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f'\n## {today}', '', f'**Source**: [[{source_name}]]']
    lines.append('**Pages created**: ' + (', '.join(f'[[{p}]]' for p in created) if created else 'none'))

    updated_pages = compute_updated_pages(related_links, conflict_links)
    if updated_pages:
        lines.append('**Pages updated**: ' + ', '.join(f'[[{p}]]' for p in updated_pages))

    entry = '\n'.join(lines) + '\n'

    existing = "# Ingest Log\n"
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, encoding="utf-8") as f:
            existing = f.read()
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(existing + entry)


def finalize(state):
    created = state["created_pages"]
    if created:
        subprocess.run(
            [sys.executable, "Scripts/semantic-search.py", "--update", ",".join(created)],
            capture_output=True,
        )
        append_to_index(created)

    append_to_log(state["source_name"], created, state["related_links"], state["conflict_links"])
    subprocess.run([sys.executable, "Scripts/check-sources.py", "mark", state["source_path"]], capture_output=True)
    clear_state()

    print("Ingest complete.")
    print(f"Source: {state['source_name']}")
    print(f"Pages created: {len(created)}")
    for p in created:
        print(f"  - {p}")
    updated_pages = compute_updated_pages(state["related_links"], state["conflict_links"])
    if updated_pages:
        print(f"Pages updated: {len(updated_pages)}")
        for p in updated_pages:
            print(f"  - {p}")

    pending = scan_unprocessed()
    if pending:
        print()
        print(f"{len(pending)} source(s) still unprocessed. Run "
              "'python3 Scripts/ingest-pipeline.py start' (no path) to continue "
              "with the next one.")


# ---------------------------------------------------------------------------
# State

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def clear_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)


def step_hint(state):
    phase = state["phase"]
    if phase == "await_concepts":
        return f"Run: python3 Scripts/ingest-pipeline.py start \"{state['source_path']}\" to see the source again, then 'concepts'."
    if phase == "link":
        return f"Run: python3 Scripts/ingest-pipeline.py start \"{state['source_path']}\" to see the current comparison again, then 'link no|related|conflict'."
    return "Run: python3 Scripts/ingest-pipeline.py start \"<source path>\" to begin a new ingest."


# ---------------------------------------------------------------------------
# Step prompts

def compute_candidates(g, same_source_slugs):
    page_path = os.path.join(WIKI_DIR, f"{g['slug']}.md")
    with open(page_path, encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'^## Content\n(.*?)(?=\n## |\Z)', content, re.MULTILINE | re.DOTALL)
    body = m.group(1).strip() if m else ""
    query = f"{g['title']} {body}"
    return [h for h in semantic_search(query)
            if h != g["slug"] and h not in same_source_slugs
            and os.path.exists(os.path.join(WIKI_DIR, f"{h}.md"))]


def advance_link_cursor(state):
    """Advance state['cursor'] to the next (group, candidate) pair needing a
    decision. Returns True if found, False if nothing left to link."""
    groups = state["groups"]
    cur = state["cursor"]
    same_source_slugs = set(state["created_pages"])
    while cur["group_idx"] < len(groups):
        if cur["candidates"] is None:
            cur["candidates"] = compute_candidates(groups[cur["group_idx"]], same_source_slugs)
            cur["candidate_idx"] = 0
        if cur["candidate_idx"] < len(cur["candidates"]):
            return True
        cur["group_idx"] += 1
        cur["candidates"] = None
    return False


def emit_link_prompt(state):
    cur = state["cursor"]
    g = state["groups"][cur["group_idx"]]
    candidate_slug = cur["candidates"][cur["candidate_idx"]]
    new_page = read_page_content(g["slug"])
    existing_page = read_page_content(candidate_slug)

    print("=== NEXT STEP ===")
    print("Checking for related/conflicting existing pages.")
    print()
    print(f"NEW PAGE: {new_page['title']}")
    print(new_page["body"])
    print()
    print(f"EXISTING PAGE: {existing_page['title']}")
    print(existing_page["body"])
    print()
    print(LINK_INSTRUCTIONS)
    print()
    print("Run one of:")
    print("  python3 Scripts/ingest-pipeline.py link no")
    print("  python3 Scripts/ingest-pipeline.py link related")
    print("  python3 Scripts/ingest-pipeline.py link conflict")


def emit_await_concepts_prompt(state):
    print(f"SOURCE: {state['source_path']}")
    print()
    print("=== NEXT STEP ===")
    print(f"Read the full source file at {state['source_path']} (use your file-reading tool, "
          f"not this script's output -- it doesn't print the source text).")
    print()
    print(RETELL_INSTRUCTIONS)
    print()
    print("When ready, run:")
    print("  python3 Scripts/ingest-pipeline.py concepts <<'EOF'")
    print("  <your concept blocks here>")
    print("  EOF")


def emit_current_step(state):
    phase = state["phase"]
    if phase == "await_concepts":
        emit_await_concepts_prompt(state)
    elif phase == "link":
        emit_link_prompt(state)
    else:
        print("This ingest is already complete.")


# ---------------------------------------------------------------------------
# Commands

def scan_unprocessed():
    result = subprocess.run(
        [sys.executable, "Scripts/check-sources.py", "scan"],
        capture_output=True, text=True,
    )
    try:
        return json.loads(result.stdout.strip())
    except Exception:
        return []


def cmd_start(source_path=None):
    if source_path is None:
        state = load_state()
        if state:
            emit_current_step(state)
            return
        pending = scan_unprocessed()
        if not pending:
            print("No unprocessed sources found. Nothing to ingest.")
            return
        source_path = pending[0]["path"]

    result = subprocess.run(
        [sys.executable, "Scripts/check-sources.py", "check", source_path],
        capture_output=True, text=True,
    )
    try:
        check = json.loads(result.stdout.strip())
    except Exception:
        fail(f"check-sources.py failed: {result.stdout} {result.stderr}")
    if not check.get("safe_to_ingest"):
        fail(f"Source is not safe to ingest: {json.dumps(check)}")

    state = load_state()
    if state:
        if state.get("source_path") != source_path:
            fail(f"Another ingest is in progress for \"{state['source_path']}\" "
                 f"({STATE_FILE}). Run 'python3 Scripts/ingest-pipeline.py abandon' "
                 f"to cancel it before starting a new one.")
        emit_current_step(state)
        return

    source_name = os.path.basename(source_path).replace(".md", "")
    state = {
        "phase": "await_concepts",
        "source_path": source_path,
        "source_name": source_name,
        "groups": [],
        "cursor": {"group_idx": 0, "candidates": None, "candidate_idx": 0},
        "created_pages": [],
        "related_links": [],
        "conflict_links": [],
    }
    save_state(state)
    emit_await_concepts_prompt(state)


def cmd_concepts():
    state = load_state()
    if not state:
        fail("No ingest in progress. Run 'start \"<source path>\"' first.")
    if state["phase"] != "await_concepts":
        fail(f"Wrong step: current phase is '{state['phase']}'. {step_hint(state)}")

    text = sys.stdin.read()

    quote_m = re.match(r'QUOTE:\s*(.+?)\s*\n', text)
    if not quote_m:
        fail("Missing 'QUOTE: <sentence>' line. Read the source file at "
             f"{state['source_path']} with your file-reading tool, then start your "
             "submission with a sentence (20+ characters) copied verbatim from it, "
             "prefixed 'QUOTE: '.")
    quote = quote_m.group(1).strip().strip('"“”\'')
    with open(state["source_path"], encoding="utf-8") as f:
        source_text = f.read()
    if len(quote) < 20 or normalize_for_match(quote) not in normalize_for_match(source_text):
        fail("The 'QUOTE: ...' line doesn't match the source file -- it doesn't look like "
             f"you've read {state['source_path']}. Read it with your file-reading tool, "
             "then copy a real sentence (20+ characters) from it verbatim into the QUOTE "
             "line, and resubmit.")

    concepts = parse_concepts_text(text)
    if not concepts:
        fail("No '## Concept: ...' blocks found in input. See the instructions from "
             "'start' for the expected format, then retry.")

    source_link = state["source_name"]
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()

    groups = []
    for c in concepts:
        slug, is_duplicate = resolve_filename(c["title"], source_link)
        if is_duplicate:
            continue
        page_content = render_page(template, c["title"], c["category"], source_link, c["content"])
        with open(os.path.join(WIKI_DIR, f"{slug}.md"), "w", encoding="utf-8") as f:
            f.write(page_content)
        groups.append({
            "id": len(groups),
            "title": c["title"],
            "category": c["category"],
            "slug": slug,
            "status": "created",
        })

    state["groups"] = groups
    state["created_pages"] = [g["slug"] for g in groups]

    if not groups:
        state["phase"] = "done"
        finalize(state)
        return

    state["phase"] = "link"
    state["cursor"] = {"group_idx": 0, "candidates": [], "candidate_idx": 0}

    if advance_link_cursor(state):
        save_state(state)
        print(f"Created {len(groups)} page(s).")
        print()
        emit_link_prompt(state)
    else:
        state["phase"] = "done"
        finalize(state)


def cmd_link(answer):
    state = load_state()
    if not state:
        fail("No ingest in progress. Run 'start \"<source path>\"' first.")
    if state["phase"] != "link":
        fail(f"Wrong step: current phase is '{state['phase']}'. {step_hint(state)}")

    answer = answer.strip().lower()
    if answer not in ("no", "related", "conflict"):
        fail("link requires 'no', 'related', or 'conflict'")

    cur = state["cursor"]
    g = state["groups"][cur["group_idx"]]
    candidate_slug = cur["candidates"][cur["candidate_idx"]]

    new_path = os.path.join(WIKI_DIR, f"{g['slug']}.md")
    existing_path = os.path.join(WIKI_DIR, f"{candidate_slug}.md")

    if answer in ("related", "conflict"):
        a = append_frontmatter_list(new_path, "related", candidate_slug)
        b = append_frontmatter_list(existing_path, "related", g["slug"])
        if a and b:
            state["related_links"].append(f"{g['slug']} <-> {candidate_slug}")

    if answer == "conflict":
        a = append_frontmatter_list(new_path, "conflicts", candidate_slug)
        b = append_frontmatter_list(existing_path, "conflicts", g["slug"])
        if a and b:
            state["conflict_links"].append(f"{g['slug']} <-> {candidate_slug}")

    cur["candidate_idx"] += 1
    if advance_link_cursor(state):
        save_state(state)
        emit_link_prompt(state)
    else:
        state["phase"] = "done"
        finalize(state)


def cmd_status():
    state = load_state()
    if not state:
        print("No ingest in progress.")
        return
    print(f"Source: {state['source_path']}")
    print(f"Phase: {state['phase']}")
    for g in state["groups"]:
        print(f"  [{g['status']}] {g['title']} ({g['category']}) -> {g['slug']}")


def cmd_abandon():
    state = load_state()
    if not state:
        print("No ingest in progress.")
        return

    removed = []
    for g in state["groups"]:
        path = os.path.join(WIKI_DIR, f"{g['slug']}.md")
        if os.path.exists(path):
            os.remove(path)
            removed.append(g["slug"])

    clear_state()

    print(f"Abandoned ingest for: {state['source_path']}")
    if removed:
        print(f"Removed {len(removed)} draft page(s):")
        for s in removed:
            print(f"  - {s}")
    print('You can now run \'start "<source path>"\' for this or another source.')


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: ingest-pipeline.py start \"<source-path>\" | concepts | link no|related|conflict | status")
        sys.exit(1)

    if args[0] == "start":
        cmd_start(args[1] if len(args) >= 2 else None)
    elif args[0] == "concepts":
        cmd_concepts()
    elif args[0] == "link":
        if len(args) < 2:
            fail("link requires 'no', 'related', or 'conflict'")
        cmd_link(args[1])
    elif args[0] == "status":
        cmd_status()
    elif args[0] == "abandon":
        cmd_abandon()
    else:
        fail(f"Unknown command: {args[0]}")
