"""End-to-end ask: question -> retrieve -> build_messages -> generate -> answer.

Phase 3 driver. Wires the full RAG path through the lib/ modules (no direct SDK
calls here): lib.retrieve (embed + Pinecone + per-article cap) -> lib.prompt_builder
(system + user prompt) -> lib.llm (NBUECSE-gpt-5-mini). Prints the model's answer.

Usage:
    python scripts/ask.py "your question here"
    python scripts/ask.py --context "your question"   # also show retrieved titles
"""
import sys, os

# Make the repo root importable so `lib` resolves when run from anywhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Windows consoles default to cp1252 and choke on curly quotes / em-dashes in
# article text; force UTF-8 so printing answers never crashes.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv()

from lib import config
from lib.retrieve import retrieve
from lib.prompt_builder import build_messages
from lib.llm import generate


def ask(question, top_k=None, show_context=False):
    """Run the full RAG pipeline for one question. Returns the answer string."""
    context = retrieve(question, top_k or config.TOP_K)
    system, user = build_messages(question, context)
    answer = generate(system, user)
    if show_context:
        print("retrieved context:")
        for m in context:
            print(f"  {m['score']:.3f}  [aid {m['article_id']}]  {m['title']}")
        print()
    return answer


def main():
    args = sys.argv[1:]
    show_context = False
    if args and args[0] == "--context":
        show_context = True
        args = args[1:]
    if not args:
        print('usage: python scripts/ask.py [--context] "your question"')
        return
    question = " ".join(args)
    print(ask(question, show_context=show_context))


if __name__ == "__main__":
    main()
