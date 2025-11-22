

import json
from pathlib import Path


from sentence_transformers import SentenceTransformer
import numpy as np

CHUNKS_FILE = Path("ingest/chunks.json")
OUTPUT_FILE = Path("ingest/embeddings.npy")
META_FILE = Path("ingest/embeddings_meta.json")


def load_chunks():
    if not CHUNKS_FILE.exists():
        print("chunks.json not found. Run chunkSave.py first.")
        return []
    try:
        text = CHUNKS_FILE.read_text(encoding="utf-8")
        return json.loads(text)
    except Exception as e:
        print("Failed to read chunks.json:", e)
        return []


def create_embeddings():
    data = load_chunks()
    if not data:
        print("No chunks to embed.")
        return

   
    model = SentenceTransformer("all-MiniLM-L6-v2")

    texts = [entry["text"] for entry in data]
    print(f"Creating embeddings for {len(texts)} chunks...")


    vectors = model.encode(texts, show_progress_bar=True)

 
    np.save(OUTPUT_FILE, vectors)

   
    META_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Saved embeddings to {OUTPUT_FILE}")
    print(f"Saved metadata to {META_FILE}")


if __name__ == "__main__":
    create_embeddings()
