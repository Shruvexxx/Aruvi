# recommender.py
import os, pickle
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = "rec_embed.pkl"

_model = None
_index = None

def _ensure_loaded():
    global _model, _index
    if _index is None:
        with open(INDEX_PATH, "rb") as f:
            _index = pickle.load(f)
        _model = SentenceTransformer(_index["model_name"])

def _cosine_topk(q_vec, mat, k=5):
    # mat and q_vec must already be L2-normalized
    sims = (mat @ q_vec.T).ravel()
    idx = np.argsort(-sims)[:k]
    return idx, sims[idx]

def get_recommendations(text: str, top_k: int = 5):
    _ensure_loaded()
    if not text or not text.strip():
        # fallback: just return first K docs (or sort by recency if you add it)
        docs = _index["docs"][:top_k]
        return [(d["title"], d["url"]) for d in docs]
    q = _model.encode([text], normalize_embeddings=True)
    embs = _index["embeddings"]
    idx, _ = _cosine_topk(q, embs, k=top_k)
    return [( _index["docs"][i]["title"], _index["docs"][i]["url"] ) for i in idx]
