"""Pure prompt construction. Imports SYSTEM_PROMPT from config. No network.

build_messages(question, context) -> (system_prompt, user_prompt). The system
prompt is config.SYSTEM_PROMPT verbatim (never re-typed here); the user prompt
packs the retrieved chunks + the question so the model answers only from context.
"""
from lib import config


def _format_context(context):
    """Retrieved chunks -> a numbered, labeled context block (string)."""
    if not context:
        return "(no relevant Medium articles were retrieved)"
    blocks = []
    for i, m in enumerate(context, 1):
        title = m.get("title", "") or "(untitled)"
        aid = m.get("article_id", "")
        authors = m.get("authors", "") or "(unknown)"
        chunk = (m.get("chunk", "") or "").strip()
        blocks.append(f"[{i}] article_id={aid} | title: {title} | authors: {authors}\n{chunk}")
    return "\n\n".join(blocks)


def build_user_prompt(question, context):
    """The per-request user message: retrieved context + the question."""
    return (
        "Answer the question using ONLY the retrieved Medium article context below.\n\n"
        "=== CONTEXT ===\n"
        f"{_format_context(context)}\n"
        "=== END CONTEXT ===\n\n"
        f"Question: {question}"
    )


def build_messages(question, context):
    """-> (system_prompt, user_prompt). Pure; system prompt comes from config."""
    return config.SYSTEM_PROMPT, build_user_prompt(question, context)
