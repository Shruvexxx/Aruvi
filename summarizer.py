# summarizer.py
import re
import numpy as np
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

def _regex_sent_tokenize(text: str) -> List[str]:
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

def _get_sentence_splitter():
    # Try NLTK; fall back to regex
    try:
        import nltk
        for pkg in ("punkt", "punkt_tab"):
            try:
                nltk.data.find(f"tokenizers/{pkg}")
            except LookupError:
                nltk.download(pkg, quiet=True)
        return nltk.sent_tokenize
    except Exception:
        return _regex_sent_tokenize

sent_tokenize = _get_sentence_splitter()

def _trim_clause(s: str) -> str:
    s = re.sub(r'\s*[\(\[].*?[\)\]]', '', s)
    s = re.sub(r'\s+—[^.?!]*', '', s)
    s = re.sub(r'\s+-[^.?!]*', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def _wc(t: str) -> int:
    return len(re.findall(r'\w+', t or ""))

def summarize_text(text: str, target_words: int = 70, max_sentences: int = 4, mmr_lambda: float = 0.75) -> str:
    text = (text or "").strip()
    if not text:
        return "No input provided."

    sents = [s for s in sent_tokenize(text) if s.strip()]
    if not sents:
        return text

    if _wc(text) <= target_words:
        return _trim_clause(text)

    # TF-IDF over sentences
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(sents)                 # scipy.sparse csr (n x v)
    Xn = normalize(X, norm="l2", axis=1)                # stays sparse

    # --- FIX 1: make doc_vec a plain ndarray (not np.matrix)
    # mean over rows → 1 x v sparse; convert to dense row vector
    doc_vec = Xn.mean(axis=0)                           # 1 x v (sparse matrix)
    doc_vec = np.asarray(doc_vec).ravel()               # ndarray shape (v,)
    denom = np.linalg.norm(doc_vec) + 1e-9
    doc_vec = doc_vec / denom                           # L2-normalize

    # Relevance: cosine = row dot normalized centroid
    # (Xn is row-normalized; doc_vec already normalized)
    rel = (Xn @ doc_vec).A.ravel() if hasattr(Xn @ doc_vec, "A") else np.asarray(Xn @ doc_vec).ravel()

    # --- FIX 2: sentence-to-sentence sim as ndarray (no np.matrix)
    S_sparse = Xn @ Xn.T                                # n x n sparse
    S = S_sparse.toarray()                              # ndarray (n x n), values 0..1

    picked, remaining, words_used = [], list(range(len(sents))), 0
    # Maximal Marginal Relevance
    while remaining and len(picked) < max_sentences and words_used < target_words + 25:
        best_i, best_score = None, -1e9
        for i in remaining:
            if not picked:
                score = rel[i]
            else:
                redundancy = float(np.max(S[i, picked]))
                score = mmr_lambda * rel[i] - (1.0 - mmr_lambda) * redundancy
            if score > best_score:
                best_i, best_score = i, score
        picked.append(best_i)
        remaining.remove(best_i)
        words_used += _wc(sents[best_i])

    picked.sort()
    pieces = [_trim_clause(sents[i]) for i in picked]
    words = " ".join(pieces).split()
    if len(words) > target_words:
        words = words[:target_words]
        if words and words[-1][-1] not in ".!?":
            words.append("...")
    return " ".join(words)
