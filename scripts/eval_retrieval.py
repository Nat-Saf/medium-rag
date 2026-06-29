"""Phase 2 retrieval sanity-check (the rag-eval skill). Prints chunks for human judgment."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from lib import config
from lib.retrieve import retrieve

QUESTIONS = [
    "Find an article that reframes marketing as a conversation with readers.",
    "List 3 articles about education.",
    "An article arguing past pandemics can spur innovation and recovery.",
    "Beginner-friendly advice on building habits that stick.",
]


def main():
    for q in QUESTIONS:
        print("\n===", q)
        for m in retrieve(q, config.TOP_K):
            print(f"  {m['score']:.3f}  {m['title'][:60]}")
            print(f"        {m['chunk'][:160].strip()}...")


if __name__ == "__main__":
    main()
