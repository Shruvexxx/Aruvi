# recommender_index_embed.py
import os, json, glob, pickle
import numpy as np
from sentence_transformers import SentenceTransformer

CORPUS_DIR = "corpus"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
OUT_PATH = "rec_embed.pkl"

def load_docs():
    docs = []
    for p in glob.glob(os.path.join(CORPUS_DIR, "*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("text"):
                docs.append(d)
        except Exception:
            continue
    return docs

def build():
    docs = load_docs()
    if not docs:
        raise SystemExit("No documents in corpus/. Run rss_ingest.py first.")
    texts = [(d.get("title","") + "\n\n" + d.get("text","")).strip() for d in docs]
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    data = {"model_name": MODEL_NAME, "embeddings": embeddings.astype(np.float32), "docs": docs}
    with open(OUT_PATH, "wb") as f:
        pickle.dump(data, f)
    print(f"Indexed {len(docs)} docs → {OUT_PATH}")

if __name__ == "__main__":
    build()
