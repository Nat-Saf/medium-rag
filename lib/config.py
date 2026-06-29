"""Central config — the single source of truth for the RAG system.

Non-secret knobs live here as plain literals; SECRETS are read from environment
variables (never hard-coded, never committed). Both ingest.py and the api/
handlers import from this one module, so GET /api/stats can never disagree with
what POST /api/prompt actually uses. The required system prompt also lives here
so prompt_builder.py imports it instead of hard-coding it.
"""
import os

# ---- LLMod model names ----
# NBUECSE-* is THIS account's provisioned namespace. The assignment PDF shows
# ZYRANGG-* as a template placeholder; each key is scoped to its own prefix, and
# our key (the 403 it returns) only allows NBUECSE-*. Same underlying models.
EMBED_MODEL = "NBUECSE-text-embedding-3-small"
CHAT_MODEL  = "NBUECSE-gpt-5-mini"
EMBED_DIM   = 1536                 # must match the Pinecone index dimension

# ---- RAG hyperparameters (reported verbatim by GET /api/stats) ----
CHUNK_SIZE    = 512                # tokens, hard cap 1024
OVERLAP_RATIO = 0.15               # 0.0 .. 0.3
TOP_K         = 8                  # 1 .. 30 (context chunks returned to the LLM)

# ---- Ingestion controls ----
MAX_PER_ARTICLE = 3                # cap chunks per article in retrieval (depth vs breadth)

NUM_ROWS    = 50                   # how many CSV rows to embed. None = full corpus.
EMBED_BATCH = 128                  # chunks per LLMod embeddings call (batching is required)

# ---- Pinecone ----
INDEX_NAME = "medium-rag"

# ---- Required system prompt (kept verbatim; a short style note is appended) ----
SYSTEM_PROMPT = (
    "You are a Medium-article assistant that answers questions strictly and only "
    "based on the Medium articles dataset context provided to you (metadata and "
    "article passages). You must not use any external knowledge, the open internet, "
    "or information that is not explicitly contained in the retrieved context. If the "
    "answer cannot be determined from the provided context, respond: \"I don't know "
    "based on the provided Medium articles data.\" Always explain your answer using "
    "the given context, quoting or paraphrasing the relevant article passage or "
    "metadata when helpful.\n\n"
    "Be concise. When asked to list articles, return distinct articles. When asked for "
    "a title and/or author, return exactly those fields."
)

# ---- Secrets: read from env (.env locally, Vercel env vars in prod) ----
LLMOD_API_KEY    = os.environ.get("LLMOD_API_KEY")
LLMOD_BASE_URL   = os.environ.get("LLMOD_BASE_URL")     # e.g. https://api.llmod.ai/v1
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")

def as_stats() -> dict:
    """The exact JSON object GET /api/stats must return."""
    return {"chunk_size": CHUNK_SIZE, "overlap_ratio": OVERLAP_RATIO, "top_k": TOP_K}
