# RESUME — where this project stands

Pick-up-here checklist for continuing the Medium RAG build on another machine.
Last updated: 2026-06-29.

## Status
**Phase 1 (offline ingest) — DONE and verified.** A 50-row subset is embedded and
live in Pinecone. The full pipeline (CSV → chunk → batch-embed → upsert) runs
end-to-end. Next up is **Phase 2 (retrieval eval)**.

Pinecone index `medium-rag`: dimension 1536, cosine, **160 vectors** (50 rows →
160 chunks at CHUNK_SIZE=512 / OVERLAP_RATIO=0.15).

## Since the last commit
- **Model namespace fixed.** Our LLMod key is provisioned for the `NBUECSE-*`
  namespace; the assignment PDF's `ZYRANGG-*` is only a template placeholder (a
  `ZYRANGG-*` call returns `403 key_model_access_denied`). Updated `EMBED_MODEL` /
  `CHAT_MODEL` in `lib/config.py` to `NBUECSE-*`, and noted the reason in
  `CLAUDE.md` and `DESIGN_NOTES.md`.
- **Ran Phase 1 ingest** on this machine: 50 rows → 160 chunks → 160 vectors
  upserted; verified via `describe_index_stats`.
- **Added the `session-resume` project skill** (`.claude/skills/session-resume/`)
  that keeps this file current before every commit.

## To resume (next: Phase 2 — retrieval eval)
1. `git pull`, then `pip install -r requirements.txt` (if a fresh machine).
2. Ensure `.env` exists at repo root (gitignored) with `LLMOD_API_KEY`,
   `LLMOD_BASE_URL`, `PINECONE_API_KEY`, `CSV_PATH`. Use a key with `NBUECSE-*`
   access. Provide `medium-english-50mb.csv` at the repo root (gitignored, ~50 MB).
3. Vectors are already live (no need to re-run ingest unless the index was cleared).
   Run the retrieval eval — retrieval only, no chat model, no extra cost:
   ```
   python scripts/eval_retrieval.py
   ```
   It prints score / title / snippet per example question. Judge whether the
   retrieved chunks are actually relevant before wiring up generation.

## After Phase 2
- Phase 3: exercise the chat model (`NBUECSE-gpt-5-mini`) via `lib/llm.py` +
  `lib/prompt_builder.py`.
- Phase 4: the API handlers (`api/prompt.py`, `api/stats.py`).
- Phase 5: tune params — chunk_size/overlap need re-embed (finalize on 50 rows
  first); top_k/max_per_article are query-time only (free to change).
- Phase 6: deploy to Vercel on the 50-row index, verify the live API, THEN run the
  full embed once (`NUM_ROWS=None`, ~$0.30). Deploy-then-scale.

## Known issues already diagnosed
1. **FIXED (in repo):** `csv.field_size_limit(sys.maxsize)` threw `OverflowError` on
   Windows; `ingest.py` steps the limit down to the largest accepted value.
2. **NOT hit on a personal laptop:** on a TLS-inspecting corporate network the first
   Pinecone/LLMod HTTPS call can fail with `CERTIFICATE_VERIFY_FAILED`. Fix if it
   recurs: `pip install truststore` + `truststore.inject_into_ssl()` at the top of
   `lib/config.py`.

## Hard constraints (from CLAUDE.md / DESIGN_NOTES.md / assignment PDF)
- chunk_size ≤ 1024, overlap_ratio ≤ 0.3, top_k ≤ 30. Total spend budget $5; embed
  in batches (never one chunk per call).
- All model calls go through the LLMod API (OpenAI SDK pointed at `LLMOD_BASE_URL`);
  models are `NBUECSE-text-embedding-3-small` (1536-d) and `NBUECSE-gpt-5-mini`.
  (PDF shows `ZYRANGG-*` as a placeholder — do NOT use it; our key needs `NBUECSE-*`.)
- Never commit secrets or the CSV.
