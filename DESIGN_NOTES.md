# DESIGN_NOTES.md — decisions & rationale

Short, durable answers to questions that came up while planning. Claude Code should
treat these as settled decisions for this repo.

## Chunking
- Chunk **per article**, never across articles. `chunk_article(row)` processes one row;
  the last chunk of an article is just the remainder (shorter than CHUNK_SIZE). No chunk
  ever contains text from two articles.
- Do **not** make one chunk per article. Median article ≈ 1,315 tokens; only ~9% are
  under 512. So most articles produce several chunks. Start at CHUNK_SIZE=512,
  OVERLAP_RATIO=0.15 (≈4 chunks/article, ~32k chunks total).

## Storage / retrieval
- Pinecone stores the **vector + metadata**. Put the chunk's text in `metadata.chunk`
  (plus article_id, title, url, authors). A query with `include_metadata=True` returns
  the chunk text itself — that's what feeds both the LLM and the API `context` field.
- Pinecone is not a document store; it returns the metadata you put in. There is no
  separate "fetch the article" step.
- `retrieve()` must **dedupe by article_id** so "list 3 articles" yields 3 distinct
  articles, not 3 chunks of one.

## Models
- `ZYRANGG-text-embedding-3-small` = OpenAI text-embedding-3-small, 1536-d output.
- `ZYRANGG-gpt-5-mini` = OpenAI gpt-5-mini (cost-efficient chat tier).
- OpenAI does not publish parameter counts for either; do not assert a number.

## System vs user prompt
- **System prompt** = fixed instructions/role/constraints (the required Medium-assistant
  text). It governs behaviour and is the same every call.
- **User prompt** = the per-request content: the retrieved chunks + the question.

## Secrets
- API keys, base URL, Pinecone key live ONLY in `.env` (local, gitignored) and Vercel
  env vars (prod). `config.py` reads them via `os.environ`. Never in CLAUDE.md or config
  literals, never committed.

## Budget discipline
- Total $5. Embed in batches (EMBED_BATCH). Tune on the NUM_ROWS subset; run the full
  embed (NUM_ROWS=None) exactly once at the end (~$0.30).

## Hyperparameter limits (hard)
- chunk_size ≤ 1024, overlap_ratio ≤ 0.3, top_k ≤ 30. `/api/stats` reports the live values.
