# recommender.py — hybrid: semantic + BM25 + recency + MMR diversity
import os, pickle, time, math
from typing import List, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import tldextract
import re

INDEX_PATH = os.getenv("ARUVI_INDEX_PATH", "rec_embed.pkl")

# weights (tweak via env if you like)
W_SEM   = float(os.getenv("ARUVI_W_SEM", "0.55"))   # semantic (cosine)
W_BM25  = float(os.getenv("ARUVI_W_BM25", "0.30"))  # keyword (BM25)
W_REC   = float(os.getenv("ARUVI_W_REC", "0.15"))   # recency
HL_DAYS = float(os.getenv("ARUVI_HALF_LIFE_DAYS", "120"))  # recency half-life
MMR_LAM = float(os.getenv("ARUVI_MMR_LAMBDA", "0.75"))     # relevance vs novelty
DOMAIN_PENALTY = float(os.getenv("ARUVI_DOMAIN_PENALTY", "0.07"))  # per-dup

_model: Optional[SentenceTransformer] = None
_index = None
_bm25  = None
_index_mtime: Optional[float] = None

_word_re = re.compile(r"[A-Za-z0-9]+")
def _tokenize(s: str):
    return [w.lower() for w in _word_re.findall(s or "")]

def _load_index():
    with open(INDEX_PATH, "rb") as f:
        d = pickle.load(f)
    d["embeddings"] = np.asarray(d["embeddings"]).astype(np.float32)
    return d

def _ensure_loaded():
    global _model, _index, _bm25, _index_mtime
    try:
        m = os.path.getmtime(INDEX_PATH)
    except FileNotFoundError:
        _index = _bm25 = _model = None
        _index_mtime = None
        return
    if _index is None or _index_mtime != m:
        _index = _load_index()
        _index_mtime = m
        _model = SentenceTransformer(_index["model_name"])
        _bm25 = BM25Okapi(_index["tok_docs"])

def _recency_score(ts: float) -> float:
    if not ts or not isinstance(ts, (int,float)):
        return 0.5
    # exponential decay with half-life HL_DAYS
    now = time.time()
    hl = HL_DAYS * 86400.0
    return 0.5 + 0.5 * math.exp(-(now - float(ts)) / hl)

def _domain(u: str) -> str:
    ext = tldextract.extract(u or "")
    return ".".join([p for p in [ext.domain, ext.suffix] if p])

def _mmr_diversify(candidates_idx: np.ndarray,
                   base_scores: np.ndarray,
                   emb: np.ndarray,
                   k: int) -> List[int]:
    """MMR: pick top-k balancing relevance and novelty in embedding space."""
    picked = []
    remaining = list(candidates_idx)
    if not len(remaining):
        return picked
    # normalize embeddings row-wise to be safe
    emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9)
    while remaining and len(picked) < k:
        best_i, best_score = None, -1e9
        for i in remaining[:50]:  # look at top-50 to keep speed
            relevance = base_scores[i]
            if not picked:
                score = relevance
            else:
                # novelty = 1 - max cosine similarity to picked
                sims = emb[i] @ emb[picked].T
                if sims.ndim == 0:
                    sims = np.array([float(sims)])
                max_sim = float(np.max(sims))
                novelty = 1.0 - max_sim
                score = MMR_LAM * relevance + (1.0 - MMR_LAM) * novelty
            if score > best_score:
                best_i, best_score = i, score
        picked.append(best_i)
        remaining.remove(best_i)
    return picked

def get_recommendations(query_text: str, top_k: int = 5) -> List[Tuple[str, str]]:
    _ensure_loaded()
    if not _index:
        # No index yet → safe defaults
        return [
            ("Popular Articles", "https://news.ycombinator.com/"),
            ("AI Basics — fast.ai", "https://www.fast.ai/"),
            ("arXiv: cs.LG (recent)", "https://arxiv.org/list/cs.LG/recent")
        ][:top_k]

    docs = _index["docs"]
    emb_mat = _index["embeddings"]
    tok_docs = _index["tok_docs"]

    # --- empty query → show recent, diversified
    q = (query_text or "").strip()
    if not q:
        order = sorted(range(len(docs)),
                       key=lambda i: _index["docs"][i].get("published_epoch", 0),
                       reverse=True)
        # light domain de-dupe
        seen = set(); out = []
        for i in order:
            dom = _domain(docs[i]["url"])
            if dom in seen: continue
            seen.add(dom)
            out.append((docs[i].get("title","(untitled)"), docs[i]["url"]))
            if len(out) >= top_k: break
        return out

    # --- query enc/score
    q_vec = _model.encode([q], normalize_embeddings=True).astype(np.float32)[0]
    sem_sims = emb_mat @ q_vec  # cosine (already normalized)

    # BM25 keyword
    q_tok = _tokenize(q)
    bm25 = np.array(_bm25.get_scores(q_tok), dtype=np.float32)
    if np.max(bm25) > 0:
        bm25 = bm25 / np.max(bm25)  # 0..1
    else:
        bm25 = np.zeros_like(bm25)

    # recency 0..1
    rec = np.array([_recency_score(d.get("published_epoch", 0)) for d in docs], dtype=np.float32)

    # domain penalty for duplicates later
    # first compute hybrid score without penalty
    base = W_SEM * sem_sims + W_BM25 * bm25 + W_REC * rec

    # preselect top-N to diversify
    N = min(max(50, top_k * 8), len(docs))
    prelim = np.argpartition(-base, N-1)[:N]
    prelim = prelim[np.argsort(-base[prelim])]

    # MMR diversify within prelim
    picked_idx = _mmr_diversify(prelim, base, emb_mat, k=top_k*3)

    # domain-aware selection
    seen_dom = {}
    final = []
    for i in picked_idx:
        dom = _domain(docs[i]["url"])
        penalty = DOMAIN_PENALTY * seen_dom.get(dom, 0)
        score = base[i] - penalty
        final.append((i, score))
        seen_dom[dom] = seen_dom.get(dom, 0) + 1

    final = sorted(final, key=lambda x: -x[1])[:top_k]

    # format and de-dup URLs
    seen_urls, results = set(), []
    for i, _ in final:
        url = docs[i]["url"].strip()
        if not url or url in seen_urls: continue
        seen_urls.add(url)
        title = (docs[i].get("title") or "(untitled)").strip()
        results.append((title, url))
        if len(results) >= top_k: break

    # still nothing? safe defaults
    if not results:
        results = [
            ("Popular Articles", "https://news.ycombinator.com/"),
            ("AI Basics — fast.ai", "https://www.fast.ai/"),
            ("arXiv: cs.LG (recent)", "https://arxiv.org/list/cs.LG/recent")
        ][:top_k]

    return results
