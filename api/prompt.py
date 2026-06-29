"""POST /api/prompt — Vercel Python serverless handler.

question -> retrieve (embed + Pinecone + per-article cap) -> build prompt ->
gpt-5-mini (via the OpenAI SDK pointed at LLMod) -> JSON. Everything is imported
from lib/ so this handler and /api/stats can never disagree about config.
"""
import os, sys, json
from http.server import BaseHTTPRequestHandler

# repo root on sys.path so `from lib import ...` resolves on Vercel
# (vercel.json ships lib/ via includeFiles — see CLAUDE.md "Vercel gotcha")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NOTE: lib imports are deferred into handle_question (not module top level).
# Vercel's Python builder imports this module to detect the `handler` variable;
# importing lib (-> openai, pinecone) at top level fails that detection step and
# yields "No python entrypoint found". Importing at request time keeps the module
# stdlib-only for detection while lib (shipped via includeFiles) loads at runtime.


def handle_question(question):
    """Shared logic -> the JSON-able response dict (per the API contract)."""
    from lib.retrieve import retrieve
    from lib.prompt_builder import build_messages
    from lib.llm import generate

    context = retrieve(question)
    system, user = build_messages(question, context)
    answer = generate(system, user)
    return {
        "response": answer,
        "context": [
            {"article_id": c["article_id"], "title": c["title"],
             "chunk": c["chunk"], "score": c["score"]}
            for c in context
        ],
        "Augmented_prompt": {"System": system, "User": user},
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("content-length", 0) or 0)
            body = self.rfile.read(length) if length else b"{}"
            question = ((json.loads(body or b"{}") or {}).get("question") or "").strip()
            if not question:
                return self._send(400, {"error": "Missing 'question' in request body."})
            self._send(200, handle_question(question))
        except Exception as e:
            self._send(500, {"error": str(e)})

    def _send(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
