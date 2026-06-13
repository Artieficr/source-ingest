# Obsidian Wiki Ingest Pipeline

This [Obsidian](https://obsidian.md) vault contains a working pipeline that turns raw clipped sources (YouTube transcripts, articles, deep-research reports, etc.) into an atomic, cross-linked wiki of small notes — one note per concept, with semantic search-driven linking between related/conflicting notes.

It's designed to be driven turn-by-turn by an LLM agent (Claude Code, Codex, Odysseus, or similar) with file-read and shell-execute tools. The pipeline script itself makes **no chat/completion model calls** — all reading, writing, and judgment calls happen in the agent's turn; the script's only model interaction is calling an Ollama embeddings endpoint for semantic search, and it otherwise just does bookkeeping and tells the agent what to do next.

## Quick start (new project)

1. `git clone https://github.com/Artieficr/source-ingest` and `git checkout 97eccff` to grab fresh state, without examples (or skip `checkout` if you want to keep them).
Or manually copy `Schema/`, `Scripts/`, this `README.md`, and an empty `Wiki/_meta/` (with header-only `index.md` and `log.md`) into your vault. 
2. Create `Sources/` with your source `.md` files, each with `processed: false` in frontmatter.
3. Run `python3 Scripts/semantic-search.py --rebuild` once (creates `Scripts/wiki-index.json`; harmless if `Wiki/` is empty).
4. Point your agent at `Schema/Skills/ingest/SKILL.md` and say "ingest `<source path>`" (or run `ingest-pipeline.py start` with no path to process sources one by one).

## Directory structure

```
Sources/                    Raw source files
Wiki/                       Generated atomic wiki pages
Wiki/_meta/index.md         Flat list of all wiki pages (auto-generated and updated)
Wiki/_meta/log.md           Append-only ingest history log (auto-generated and updated)
Schema/Templates/wiki-page-template.md   Page template used by the pipeline
Schema/Skills/ingest/SKILL.md            Agent-facing instructions ("how to ingest")
Scripts/check-sources.py    Tracks which sources are processed
Scripts/semantic-search.py  Embedding-based search/index over Wiki/
Scripts/ingest-pipeline.py  The pipeline state machine itself
Scripts/wiki-index.json     Embedding index (auto-generated)
```

`Sources/` and `Wiki/` contain examples of how sources get ingested into the wiki.
The schema, skills, and scripts are meant to be reused across projects.
To use this fresh, recreate empty `Sources/` (any `.md` files with frontmatter, `processed: false`) and an empty `Wiki/_meta/index.md` / `Wiki/_meta/log.md`.

## How a source file looks

Any Markdown file with YAML frontmatter works. The only field the pipeline cares about is `processed`:

```yaml
---
title: Some Source Title
processed: false
---
... source content ...
```

`check-sources.py scan` finds all `.md` files under `Sources/` (recursively) with `processed: false` (or missing). `check-sources.py mark`/`unmark` flips the flag.

## How a wiki page looks

Every generated page follows `Schema/Templates/wiki-page-template.md`:

```markdown
---
title: "{{TITLE}}"
aliases:
  - "{{TITLE}}"
category: {{CATEGORY}}
source: "[[{{SOURCE_NAME}}]]"
created: {{CREATED_DATE}}
related: []
conflicts: []
---
# {{TITLE}}

## Content
{{BODY}}
```

- `category` is one of: `technique`, `tool`, `background`, `typology`, `effect`, `other`.
	- `technique` — a named method or procedure (a how-to).
	- `tool` — a named product, API, or specific entity (a what).
	- `background` — a person, project, historical event, or etymology (context/origin info).
	- `typology` — a categorized list of named types or styles (a taxonomy).
	- `effect` — a named effect, phenomenon, or concept (a why/what-happens).
	- `other` — anything substantial that doesn't fit the above.
- `related` / `conflicts` are flow-style YAML lists of Obsidian wikilinks, e.g. `related: ["[[some-other-page]]", "[[another-page]]"]`. The pipeline appends to these lists mechanically (regex-based) — it never rewrites page content to add links.
- `## Content` holds the extractive/retold body (roughly 100-800 words). Embeddings for semantic search are computed on everything *after* the frontmatter, so `related`/`conflicts` never influence search results.

## The pipeline: `Scripts/ingest-pipeline.py`

A small CLI state machine, state persisted in `Scripts/.ingest-state.json` so an interrupted ingest can be resumed. It makes no chat/completion model calls itself (only the embeddings call described below) — every judgment call is made by the calling agent, one bounded step at a time.

### Commands

- `start ["<source path>"]` — begin (or resume) an ingest. With no path, resumes any in-progress ingest, or else picks the next unprocessed source via `check-sources.py scan`. Prints instructions for the next step; never prints the source text itself (the agent reads the file with its own tools).
- `concepts` (stdin) — submit the concept-grouped retelling. Creates one wiki page per concept.
- `link no|related|conflict` — judge the relationship between a newly created page and one existing page found via semantic search.
- `status` — show current progress.
- `abandon` — cancel the in-progress ingest, removing any pages it already created, so a new ingest can start cleanly.

### Phase 1 — Retell & create pages (`await_concepts` → `concepts`)

1. `start "<source path>"` prints the **retelling instructions**: read the full source file with your own file-reading tool, then write a concept-grouped prose retelling — one `## Concept: <title>` block per concept, each with a `Category:` line and a 100-800 word extractive body. Group by idea, not by the source's original structure (a 3-heading article might become 8 concepts).

2. **Anti-hallucination check**: the submission to `concepts` must start with a line `QUOTE: <verbatim sentence from the source>` (20+ characters). The script normalizes both this quote and the full source file (strips markdown emphasis chars, collapses whitespace, lowercases) and does a plain substring check. If the quote isn't found in the source, the submission is rejected with instructions to actually read the file and resubmit. This is a purely mechanical check — it can't verify the retelling is faithful, only that the agent touched the real file content.

3. For each `## Concept:` block, the script:
   - Slugifies the title to a filename. If a page with that slug already exists from a *different* source, appends `--2`, `--3`, etc. If it already exists from the *same* source (idempotent rerun), skips it.
   - Fills in `Schema/Templates/wiki-page-template.md` with the title, category, source link, date, and body — script string-substitution, no model call.

4. **Same-source interconnection**: if more than one page was created from this source, every pair is mechanically cross-linked via `related` (`interconnect_same_source`) — pages extracted from the same source are always considered at least related, so this skips per-pair link judgment for them entirely.

### Phase 2 — Link judgment (`link` phase)

For each newly created page, the script runs `semantic-search.py` (threshold 0.6, top 15) against the rest of the wiki, excluding same-source siblings (already linked in phase 1) and the page itself. For each hit:

1. The script prints both pages' full `## Content` bodies.
2. The agent reads both in full and judges:
   - `link no` — not actually about the same concept (a semantic-search false positive on a full read). No link recorded.
   - `link related` — same/overlapping concept, a reader of one would benefit from the other, but no contradiction. Both pages get `related` updated.
   - `link conflict` — related *and* they state contradicting facts/numbers/claims about the same specific point. Both pages get `related` **and** `conflicts` updated.
3. Links are applied via `append_frontmatter_list` — a regex-based, single-line rewrite of the flow-style `related:`/`conflicts:` list. Never a full page rewrite.

### Finalization

Once all groups and all link candidates are processed:

- `semantic-search.py --update <new pages>` adds the new pages to the embedding index.
- New pages are appended to `Wiki/_meta/index.md`.
- A dated entry is appended to `Wiki/_meta/log.md` (source, pages created, same-source interconnection note, related/conflict links, pages updated).
- The source file's `processed` flag is flipped to `true` via `check-sources.py mark`.
- State file is cleared, and the script reports how many sources remain unprocessed.

## Semantic search: `Scripts/semantic-search.py`

- Embeddings via Ollama (`bge-m3` model, `OLLAMA_EMBEDDINGS_URL`, default `http://localhost:11434/api/embeddings`).
- `extract_text()` strips YAML frontmatter before embedding, so `related`/`conflicts` lists don't pollute the vector.
- Cosine similarity against `Scripts/wiki-index.json` (a flat `{page_slug: embedding}` map).
- `DEFAULT_THRESHOLD = 0.6` — minimum cosine similarity for a hit to be surfaced as a link candidate.
- Modes: `"query" [top_n] [--threshold T]` (search), `--rebuild` (rebuild the whole index from `Wiki/`), `--update "page1,page2"` (incrementally add pages).

## The agent-facing skill: `Schema/Skills/ingest/SKILL.md`

This is what an agent reads to know how to drive the pipeline. Summary:

1. User says "ingest `<source path>`".
2. Run `python3 Scripts/ingest-pipeline.py start "<source path>"`.
3. Treat every printed output as a fresh, self-contained step — do what it says, run the command it tells you to run, read the new output as if for the first time. No need to plan ahead.
4. When it prints "Ingest complete.", report the summary (pages created, related/conflict links) to the user.

Paths in this vault's SKILL.md are relative to the vault root (this is where the agent's working directory is). If migrating this skill into a sandboxed agent environment (e.g. Odysseus, where the vault is mounted at `/app/vault/`), paths in the skill instructions need to be adjusted accordingly — the scripts themselves use only cwd-relative paths and don't need any changes.

## Model size requirements

This pipeline was validated end-to-end with **`qwen3:32b`** running locally via Ollama, driving an agent through a full ingest to successful completion.

**Smaller local models (≤14B, e.g. `qwen3:8b`, `qwen3:14b`, `gemma4:12b`, `mistral-nemo:12b`, `llama3.2:11b`) did not perform this task reliably** — they struggled with the multi-step, tool-using, instruction-following nature of the ingest flow (correctly grouping concepts, producing a genuinely verbatim `QUOTE:` line on the first try, following the "run the command this output tells you to run" loop). Only the 32B model completed an ingest successfully in testing. If running fully local, budget for a 32B-class model; cloud/frontier models (Claude, GPT-4-class) handle this without issue.