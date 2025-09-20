# recommender_index_embed.py — build hybrid index (emb + tokens)
import os, json, glob, pickle, re, time
import numpy as np
from sentence_transformers import SentenceTransformer

CORPUS_DIR = "corpus"
MODEL_NAME = os.getenv("ARUVI_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OUT_PATH = "rec_embed.pkl"

def _load_docs():
    docs = []
    for p in glob.glob(os.path.join(CORPUS_DIR, "*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            text = (d.get("text") or "").strip()
            title = (d.get("title") or "").strip()
            url = (d.get("url") or "").strip()
            ts = d.get("published") or d.get("published_epoch") or 0
            if not text or not url:
                continue
            docs.append({
                "title": title, "url": url, "text": text,
                "published_epoch": ts if isinstance(ts, (int,float)) else 0
            })
        except Exception:
            continue
    return docs

_word_re = re.compile(r"[A-Za-z0-9]+")
def _tokenize(s: str):
    return [w.lower() for w in _word_re.findall(s or "")]

def build():
    docs = _load_docs()
    if not docs:
        raise SystemExit("No documents in corpus/")

    # text used for embedding
    texts = [(d["title"] + "\n\n" + d["text"]).strip() for d in docs]
    # tokenized docs for BM25
    tok_docs = [_tokenize(d["title"] + " " + d["text"]) for d in docs]

    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(
        texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True
    ).astype(np.float32)

    data = {
        "model_name": MODEL_NAME,
        "embeddings": embeddings,
        "docs": docs,
        "tok_docs": tok_docs,
        "built_at": int(time.time())
    }
    with open(OUT_PATH, "wb") as f:
        pickle.dump(data, f)
    print(f"Indexed {len(docs)} docs → {OUT_PATH}")

if __name__ == "__main__":
    build()
