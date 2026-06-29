# CLAUDE.md — Medium Article RAG Assistant

Instructions for Claude Code working in this repo. Read this before writing code.
See DESIGN_NOTES.md for rationale behind these decisions.

## What this project is
A Retrieval-Augmented Generation assistant that answers questions **only** from a
dataset of ~7,600 English Medium articles (`medium-english-50mb.csv`, columns:
`title, text, url, authors, timestamp, tags`). It must never use outside knowledge.

Two runtimes:
- **Offline** (`ingest.py`, run once locally): CSV → chunk → batch-embed → upsert to Pinecone.
- **Online** (`api/`, deployed on Vercel): question → embed → retrieve top-k → generate → JSON.

## Hard constraints (do not violate)
- `chunk_size` ≤ 1024 tokens, `overlap_ratio` ≤ 0.3, `top_k` ≤ 30.
- Total spend budget is **$5**. Embed in **batches**, never one chunk per call.
  Validate on a small `NUM_ROWS` subset before scaling to the full corpus.
- Embedding model: `NBUECSE-text-embedding-3-small` (1536 dims).
  Chat model: `NBUECSE-gpt-5-mini`.
  (The assignment PDF lists `ZYRANGG-*` as a template placeholder; our provisioned
  key is scoped to the `NBUECSE-*` namespace — same underlying models.)

## Module boundaries (keep these clean)
- `lib/config.py` — the ONLY place hyperparameters, model names, the index name, and the
  required **SYSTEM_PROMPT** live. Secrets are read from env vars here; never hard-code keys.
- `lib/chunking.py` — token-aware splitting only. No network. Chunks never cross articles.
- `lib/embed.py` — the ONLY file that calls LLMod **embeddings**.
- `lib/llm.py` — the ONLY file that calls LLMod **chat** (gpt-5-mini).
- `lib/db.py` — the ONLY file that touches **Pinecone** (ensure_index / upsert / query).
- `lib/retrieve.py` — orchestrates embed + db.query + per-article capping. No direct SDK calls.
- `lib/prompt_builder.py` — pure functions: builds system + user prompt. Imports
  SYSTEM_PROMPT from config. No network.
- `ingest.py` — offline entry point.
- `api/prompt.py`, `api/stats.py` — online entry points (Vercel serverless handlers).

If a change would make `prompt_builder.py` call the network, or make `retrieve.py`
import the Pinecone SDK directly, stop — that breaks the architecture.

## The system prompt lives in config
`prompt_builder.build_messages()` returns `(config.SYSTEM_PROMPT, user_prompt)`. Do not
re-type the system prompt anywhere else; edit it in `config.py` only. It already contains
the required text verbatim plus a short style note.

## API contracts
`POST /api/prompt`  in: `{"question": "..."}`  out:
```json
{"response":"...","context":[{"article_id":"...","title":"...","chunk":"...","score":0.0}],
 "Augmented_prompt":{"System":"...","User":"..."}}
```
`GET /api/stats` returns exactly `{"chunk_size":int,"overlap_ratio":float,"top_k":int}`
(read straight from `config.as_stats()`).

## Retrieval: cap per article, do NOT collapse to one
Pinecone returns chunks; several may belong to one article. `retrieve.py` keeps at most
`MAX_PER_ARTICLE` (default 3) chunks per article and returns up to `TOP_K` chunks total.
This keeps DEPTH for single-article questions (summary / precise fact / recommendation
want multiple chunks of the SAME article) while keeping BREADTH so "list 3 distinct
articles" still works. Never dedupe down to one chunk per article — that breaks summaries.
The system prompt instructs the model to return distinct articles for listing questions.

## Conventions
- Python, OpenAI SDK pointed at `LLMOD_BASE_URL`, `pinecone` client.
- Article id = the CSV row index. Vector id = `{article_id}-c{chunk_index}` (e.g. `42-c3`).
- `chunk_article(article_id, row)` returns `[{id, chunk, metadata}]`; metadata stores
  `article_id, title, url, authors, chunk` so the API returns context without a 2nd lookup.
- Never print or commit secrets. Never commit the CSV.

## Vercel gotcha
Each Python function in `api/` imports `lib/`. `vercel.json` uses
`functions["api/**/*.py"].includeFiles = "lib/**"` so lib ships with the functions, and the
handlers add the repo root to `sys.path`. If imports fail on Vercel, that's the place to look.

## Build order (one phase per session — see docs/CLAUDE_CODE_GUIDE.md)
0 setup → 1 ingest subset → 2 eval retrieval → 3 add gpt-5-mini → 4 build API →
5 tune params → 6 scale + deploy.
