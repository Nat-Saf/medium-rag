"""Offline pipeline: CSV -> chunk -> batch-embed -> upsert to Pinecone. Run once locally."""
import csv, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
csv.field_size_limit(sys.maxsize)

from dotenv import load_dotenv
load_dotenv()

from lib import config
from lib.chunking import chunk_article
from lib.embed import embed_texts
from lib import db

CSV_PATH = os.environ.get("CSV_PATH", "medium-english-50mb.csv")


def main():
    db.ensure_index()

    records = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if config.NUM_ROWS is not None and i >= config.NUM_ROWS:
                break
            records.extend(chunk_article(i, row))
    print(f"Rows read: up to {config.NUM_ROWS} | chunks produced: {len(records)}")

    vectors = embed_texts([r["chunk"] for r in records])      # batched
    payload = [{"id": r["id"], "values": v, "metadata": r["metadata"]}
               for r, v in zip(records, vectors)]
    n = db.upsert(payload)
    print(f"Upserted {n} vectors to index '{config.INDEX_NAME}'.")


if __name__ == "__main__":
    main()
