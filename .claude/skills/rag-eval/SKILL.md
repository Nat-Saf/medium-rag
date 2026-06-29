---
name: rag-eval
description: >-
  Evaluate retrieval quality for the Medium RAG project — embed test questions,
  query Pinecone via lib/retrieve.py, and print each returned chunk's score,
  title, and a snippet for the user to judge relevance. Retrieval ONLY; never
  calls the chat model. Use when the user says things like "test the retrieval",
  "eval retrieval", "check retrieval quality", "are we pulling the right chunks",
  "rag eval", or asks to sanity-check what Pinecone returns for some questions.
---

# rag-eval — retrieval-only sanity check

Run a handful of test questions through the retrieval path and print, per question,
each returned chunk's **score**, **title**, and a short **snippet** so the user can
eyeball whether the right articles came back. This is a human-judgment loop: you
surface the chunks, the user decides if they're relevant.

## Hard rule: retrieval only
- Call **only** `lib/retrieve.py` (which internally uses `lib/embed.py` + `lib/db.py`).
- **Never** import or call `lib/llm.py`, the chat model, or `prompt_builder`. No answer
  generation. This skill must not spend chat-model budget — it only embeds + queries.
- `retrieve()` already embeds the question, queries Pinecone, and caps per article
  (`MAX_PER_ARTICLE`) — do not re-implement that here.

## Prerequisites (check first, fail clearly)
1. Secrets must be loaded: `LLMOD_API_KEY`, `LLMOD_BASE_URL`, `PINECONE_API_KEY`
   (from `.env` via `python-dotenv`). If missing, tell the user and stop.
2. `lib/` must be an importable package (`lib/__init__.py` exists) and the modules
   (`config.py`, `embed.py`, `db.py`, `retrieve.py`) must live under `lib/`. If the
   code is still flat at the repo root, say so — imports will fail until the move.
3. The Pinecone index must already be populated (run `ingest.py` first). If `retrieve()`
   returns nothing for every question, suspect an empty/wrong index, not bad questions.

## How to run
Prefer the project's eval script if it exists (`scripts/eval_retrieval.py`); otherwise
run the inline snippet below. Use the questions the user gives you; if they give none,
use the default set.

Run from the repo root so `lib` is importable:

```bash
python scripts/eval_retrieval.py
```

If there's no script, run this equivalent inline (retrieval only — note there is no
import of llm/chat anywhere):

```python
import sys, os
sys.path.insert(0, os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()

from lib import config
from lib.retrieve import retrieve

QUESTIONS = [
    "Find an article that reframes marketing as a conversation with readers.",
    "List 3 articles about education.",
    "An article arguing past pandemics can spur innovation and recovery.",
    "Beginner-friendly advice on building habits that stick.",
]

for q in QUESTIONS:
    print("\n===", q)
    results = retrieve(q, config.TOP_K)
    if not results:
        print("  (no chunks returned — is the index populated?)")
        continue
    for m in results:
        print(f"  {m['score']:.3f}  {m['title'][:60]}")
        print(f"        {m['chunk'][:160].strip()}...")
```

## Output to give the user
For each question, print one block:
- The question header.
- One line per returned chunk: `score  title` then an indented ~160-char snippet.
- Results come back sorted by score (descending); keep that order.

Then add a brief, plain-English read on each question: do the top chunks look on-topic,
is the score spread reasonable, and for "list N" questions did distinct articles come
back? Flag anything that looks off (all-low scores, duplicate articles dominating,
empty results) — but leave the final relevance call to the user.

## Notes
- To test different questions, ask the user for them or edit the `QUESTIONS` list.
- Dedupe/capping is `retrieve()`'s job (`MAX_PER_ARTICLE`); don't collapse to one chunk
  per article here — summaries need multiple chunks of the same article.
