"""Compose embed + db.query + per-article capping. No direct SDK calls.

Strategy: over-fetch a pool of nearest chunks, then keep at most MAX_PER_ARTICLE
chunks per article and return up to TOP_K total. This gives DEPTH (several chunks
of the most relevant article -> good summaries / fact / recommendation) while
keeping BREADTH (no single article monopolizes the context -> "list 3 distinct"
still works). We do NOT collapse to one chunk per article.
"""
from lib import config
from lib.embed import embed_texts
from lib import db


def retrieve(question, top_k=None, max_per_article=None):
    """question -> [{article_id, title, chunk, score}], up to top_k chunks,
    at most max_per_article chunks from any single article."""
    top_k = top_k or config.TOP_K
    max_per_article = config.MAX_PER_ARTICLE if max_per_article is None else max_per_article

    vec = embed_texts([question])[0]
    pool = db.query(vec, min(top_k * 3, 30))      # over-fetch (Pinecone cap is 30)

    counts, out = {}, []
    for m in pool:                                 # already sorted by score desc
        md = m.get("metadata", {}) or {}
        aid = md.get("article_id", m["id"])
        if counts.get(aid, 0) >= max_per_article:
            continue                               # cap per article; don't drop to 1
        counts[aid] = counts.get(aid, 0) + 1
        out.append({"article_id": aid, "title": md.get("title", ""),
                    "authors": md.get("authors", ""), "url": md.get("url", ""),
                    "chunk": md.get("chunk", ""), "score": m["score"]})
        if len(out) >= top_k:
            break
    return out
