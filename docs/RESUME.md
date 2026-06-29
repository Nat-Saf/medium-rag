# RESUME — where this project stands

Pick-up-here checklist for continuing the Medium RAG build on another machine.
Last updated: 2026-06-29.

## Status
**DEPLOYED & LIVE on Vercel — verified end-to-end.** Live URL:
**https://medium-rag-gvot.vercel.app** (`POST /api/prompt`, `GET /api/stats`).
All 4 assignment questions return the correct article + author with the exact
contract shape; the nonsense question returns the exact refusal string; `/api/stats`
returns `{"chunk_size":512,"overlap_ratio":0.15,"top_k":8}`. Verified by curling the
live deployment (commit 817767a).

**PROJECT COMPLETE.** All phases done: full corpus embedded, deployed, and
validated. No parameter tuning needed — params are final.

Pinecone index `medium-rag`: dimension 1536, cosine, CHUNK_SIZE=512, OVERLAP=0.15,
**26,507 vectors (full ~7,600-article corpus)**. KEEP INDEX ACTIVE until graded.
NUM_ROWS=None. The deployed API reads live from Pinecone (scaling needs no redeploy).

### Final validation (20-case suite vs the live URL, full corpus)
- Precise fact (title+author): 6/6 ✅ · Listing 3 distinct: 4/4 ✅ · Summary: 4/4 ✅
  · Recommendation: 4/4 ✅ · Refusal exact-string: 1/2 (both refused correctly; one
  explained instead of emitting the exact sentence — guardrail held, no outside
  knowledge leaked). 19/20 clean.
- Decision: leave the refusal wording as-is (tightening risks over-refusal on valid
  partial answers). Params (512 / 0.15 / top_k 8 / max_per_article 3) are FINAL — no
  re-embed.

Submission deliverable: `Medium_RAG_Submission.docx` (1-page; live URL + GitHub URL
at top, work summary below).

## Since the last commit
- **Added `scripts/ask.py`** — end-to-end driver (question → retrieve → build_messages
  → generate → print answer). Self-contained; forces UTF-8 stdout (Windows cp1252
  mangles curly quotes/em-dashes when printing, though stored data is clean).
- **Scaled the index 50 → 200 → 1000 rows** and re-ran retrieval eval at each step.
  Findings: Q1 (marketing) robust at rank 1 everywhere; Q4 (habits) strong once
  dedicated habit articles appeared; Q3 (pandemics) recall improved but precision
  diluted by COVID near-matches (LLM still picks the right one); Q2 (education) stays
  weak — this corpus is genuinely thin on education, likely needs full corpus.
- **SYSTEM_PROMPT clarification (`lib/config.py`)** — emit the exact "I don't know…"
  sentence ONLY when nothing answers; never prefix it to a real answer. Fixed false
  refusals on Q1/Q2 and made the nonsense question return the exact string verbatim.
- **Author/url passthrough (`lib/retrieve.py` + `lib/prompt_builder.py`)** — authors
  were in Pinecone metadata but `retrieve()` dropped them, so "provide the author"
  questions failed. Now carried through to the prompt; Q1/Q3/Q4 return real authors.

## To resume (next: import to Vercel)
1. `git pull`; `pip install -r requirements.txt`; `.env` at repo root with
   `LLMOD_API_KEY`, `LLMOD_BASE_URL`, `PINECONE_API_KEY`, `CSV_PATH` (NBUECSE-scoped
   key). Provide `medium-english-50mb.csv` (gitignored). Vectors already live.
2. Sanity-check anytime: `python scripts/ask.py "your question"` (add `--context` to
   see retrieved titles), or `python scripts/eval_retrieval.py` for retrieval-only.
3. Local API smoke test without Node/vercel: a faithful runner pattern serves the
   real handlers on http://127.0.0.1:3000 (see scratchpad `local_api.py` from the
   Phase 4 session). PowerShell + curl.exe: write the JSON body to a file and POST
   with `--data "@body.json"` (PS 5.1 strips inline embedded quotes).
4. **Import to Vercel** (dashboard → Add New Project → import Nat-Saf/medium-rag):
   - Framework preset "Other", no build command; `vercel.json` ships `lib/**`.
   - Set env vars in the dashboard BEFORE deploy: `LLMOD_API_KEY`, `LLMOD_BASE_URL`,
     `PINECONE_API_KEY`. Do NOT set CSV_PATH / upload the CSV (online API doesn't
     need it). Secrets are NOT in git — they must be entered in Vercel.
   - After deploy, re-run the curl tests against the live URL.

## Remaining work
- Phase 5 (optional): tune params — chunk_size/overlap need re-embed (finalize on
  subset first); top_k/max_per_article are query-time only (free to change). If you
  change top_k/overlap, /api/stats reflects it automatically; push to redeploy.
- Phase 6 (final, the one big spend): run the full-corpus embed once locally with
  `NUM_ROWS=None` (~$0.30). The LIVE API reads from Pinecone, so scaling needs NO
  redeploy — new vectors appear to the deployed app automatically. This is what makes
  Q2 (education) and the precise pandemic article land better.

## Vercel deploy config (how it actually works — do not regress)
- `vercel.json` uses legacy `builds` (`@vercel/python`, includeFiles=lib/**) PLUS a
  `routes` block mapping `/api/prompt`->`/api/prompt.py`, `/api/stats`->`/api/stats.py`.
  The modern zero-config builder does NOT work here (rejects 2 api handler files).
- Env vars (LLMOD_API_KEY, LLMOD_BASE_URL, PINECONE_API_KEY) are set in the Vercel
  dashboard (NBUECSE-scoped key). Every push to main auto-redeploys.

## Open notes / decisions
- **Q2 "Return only the titles"** — model still appends an explanation (the required
  "Always explain" clause vs. "only titles"). Soft style issue; left as-is for now.
- **Budget:** cumulative embeds still well under ~$0.15 of the $5. The full-corpus
  embed (~$0.30) is the one big spend, saved for deploy time.
- `article_id` = 0-based CSV data-record index (`excel_row = article_id + 2`). Verify
  retrieval by title/URL, not spreadsheet row number.

## Known issues already diagnosed
0. **FIXED:** Vercel build failed with "No python entrypoint found in default
   locations, but found potential entrypoints: api/prompt.py / api/stats.py"
   (CLI 54.x). Real cause: the new zero-config Python builder won't auto-route TWO
   `/api` handler files as separate functions — it wants a single app entrypoint.
   (Deferring the `lib` imports did NOT help — the builder finds `handler` via static
   analysis, not import.) Fix: force the classic builder in `vercel.json` via
   `builds: [{src:"api/*.py", use:"@vercel/python", config:{includeFiles:"lib/**"}}]`,
   which natively supports the multi-file /api convention. The deferred `lib` imports
   were kept (harmless, fine under either builder). NOTE: legacy `builds` serves the
   functions WITH the `.py` extension and does not auto-strip it, so clean URLs 404 —
   add a `routes` block mapping `/api/prompt`->`/api/prompt.py` and `/api/stats`->
   `/api/stats.py`. Functions themselves verified working (stats.py returned 200).
1. **FIXED:** `csv.field_size_limit(sys.maxsize)` OverflowError on Windows; `ingest.py`
   steps the limit down to the largest accepted value.
2. **Not hit on a personal laptop:** corporate TLS interception can cause
   `CERTIFICATE_VERIFY_FAILED` on the first Pinecone/LLMod call. Fix if it recurs:
   `pip install truststore` + `truststore.inject_into_ssl()` atop `lib/config.py`.

## Hard constraints (from CLAUDE.md / DESIGN_NOTES.md / assignment PDF)
- chunk_size ≤ 1024, overlap_ratio ≤ 0.3, top_k ≤ 30. Budget $5; embed in batches.
- Models go through LLMod (OpenAI SDK at `LLMOD_BASE_URL`):
  `NBUECSE-text-embedding-3-small` (1536-d) and `NBUECSE-gpt-5-mini`. The PDF's
  `ZYRANGG-*` is a placeholder — do NOT use it; our key needs `NBUECSE-*`.
- Never commit secrets or the CSV.
