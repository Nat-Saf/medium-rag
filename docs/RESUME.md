# RESUME — where this project stands

Pick-up-here checklist for continuing the Medium RAG build on another machine.
Last updated: 2026-06-29.

## Status
Project reorganized to match `CLAUDE.md` (lib/ package, api/ handlers, scripts/, infra files).
Imports verified (py_compile + import smoke test). **Phase 1 (offline ingest) not yet completed
on a successful run** — see blockers below.

Last commit on `main` when this was written: the `ingest.py` Windows fix.

## Known issues already diagnosed
1. **FIXED (in repo):** `csv.field_size_limit(sys.maxsize)` threw `OverflowError` on Windows
   (C long is 32-bit). `ingest.py` now steps the limit down to the largest accepted value —
   cross-platform safe.
2. **NOT fixed (environment-specific):** running ingest on a TLS-inspecting corporate network
   gave `httpx.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] self-signed certificate in
   certificate chain` on the first Pinecone HTTPS call. Cause: a corporate proxy re-signs TLS
   with a root CA that Python's `certifi` bundle doesn't trust (affects both Pinecone and LLMod).
   A home/normal network likely won't hit this. If it recurs, fix with:
   ```
   pip install truststore
   ```
   then add to the top of `lib/config.py`:
   ```python
   try:
       import truststore
       truststore.inject_into_ssl()   # trust the OS/corporate certificate store
   except Exception:
       pass
   ```

## To resume (offline ingest, phase 1)
1. `git clone` / `git pull` this repo.
2. `pip install -r requirements.txt`
3. Create `.env` (gitignored — never commit it) with:
   ```
   LLMOD_API_KEY=<your LLMod key>
   LLMOD_BASE_URL=https://api.llmod.ai/v1      # if requests 404, drop the /v1
   PINECONE_API_KEY=<your Pinecone key>
   CSV_PATH=medium-english-50mb.csv
   ```
   NOTE: the keys used during development were shared in plaintext — generate fresh ones and
   use those here.
4. Provide the dataset `medium-english-50mb.csv` at the repo root (gitignored, ~50 MB — copy it
   over; it is not in the repo).
5. `lib/config.py` already has `NUM_ROWS=50` (validation subset, per the $5 budget). Run:
   ```
   python ingest.py
   ```
   Expected output: rows read (up to 50), chunks produced, vectors upserted to index `medium-rag`.

## After a successful ingest
- Retrieval eval: `python scripts/eval_retrieval.py` (or the `rag-eval` skill) — prints score /
  title / snippet per question; retrieval only, no chat model.
- Then exercise the API handlers (`api/prompt.py`, `api/stats.py`) and tune params.
- Build order (`CLAUDE.md`): 0 setup → 1 ingest → 2 eval → 3 chat → 4 API → 5 tune → 6 scale+deploy.

## Hard constraints (from CLAUDE.md / DESIGN_NOTES.md)
- chunk_size ≤ 1024, overlap_ratio ≤ 0.3, top_k ≤ 30. Total spend budget $5; embed in batches.
- All model calls go through the LLMod API (OpenAI SDK pointed at `LLMOD_BASE_URL`); models are
  `ZYRANGG-text-embedding-3-small` (1536-d) and `ZYRANGG-gpt-5-mini`. Never commit secrets or the CSV.
