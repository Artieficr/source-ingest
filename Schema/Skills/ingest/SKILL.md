---
name: ingest-source
description: Ingest a source file into the wiki as atomic, single-source pages.
version: 3.1.0
---

# Ingest Source

## When to Use

The user says "ingest <source path>" (or similar), pointing at a file under
`Sources/`.

## Procedure

Run:

```
python3 Scripts/ingest-pipeline.py start "<source path>"
```

This prints instructions for the next step and tells you exactly which
command to run when you're done — it does not print the source text itself.
Follow those instructions, run the command it gives you, then do the same
with whatever it prints next.

Treat each step as a fresh, self-contained task: do what the current output
says, run the command it tells you to run, and read the new output as if for
the first time. You don't need to plan ahead or remember earlier steps.

The steps you'll move through are:

1. **Retell the source** — read the full source file yourself, then write a
   concept-grouped prose retelling and pass it to `concepts` (creates one
   wiki page per concept directly -- no separate rewrite step). Your
   submission must start with a `QUOTE: <verbatim sentence from the source>`
   line — `concepts` checks this against the source file and rejects the
   submission if it doesn't match, as proof you actually read the file rather
   than guessing from the filename.
2. **Related/conflict check** — for each existing page the script finds via
   semantic search (above the similarity threshold), answer `link no`,
   `link related`, or `link conflict` for whether the new page is unrelated
   to, related to, or directly conflicts with that existing page. Pages
   created from the same source in step 1 are automatically interconnected
   and are not included in this check.

When the script prints "Ingest complete.", report that summary (pages
created, related/conflict links) to the user. Don't edit any wiki pages
directly — all writes happen through the script.

## If something goes wrong

- If interrupted partway through, run the same `start "<source path>"`
  command again — it resumes from `Scripts/.ingest-state.json` and re-prints
  the current step's prompt.
- Run `python3 Scripts/ingest-pipeline.py status` to see progress.
- If the source is already marked `processed: true`, the script will refuse
  to run — ask the user whether they want to re-ingest (in which case unmark
  it first with `python3 Scripts/check-sources.py unmark "<source path>"`).
