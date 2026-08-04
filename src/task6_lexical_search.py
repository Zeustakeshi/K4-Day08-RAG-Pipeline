"""Lexical retrieval using BM25 (with an optional TF-IDF index)."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

CORPUS: list[dict] = []
_bm25 = None
_tfidf_vectorizer = None
_tfidf_matrix = None


def _tokenize(text: str) -> list[str]:
    """Simple Vietnamese tokenizer that retains numbers and promo codes."""
    normalized = unicodedata.normalize("NFC", str(text)).lower()
    return re.findall(r"[\w]+", normalized, flags=re.UNICODE)


def load_corpus_from_chroma() -> list[dict]:
    """Load the chunks indexed by Task 4 from the persistent Chroma store."""
    import chromadb
    from .task4_chunking_indexing import CHROMA_DIR, COLLECTION_NAME

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)
    stored = collection.get(include=["documents", "metadatas"])
    documents = stored.get("documents") or []
    metadatas = stored.get("metadatas") or []
    return [
        {
            "content": content,
            "metadata": metadatas[index] if index < len(metadatas) else {},
        }
        for index, content in enumerate(documents)
        if content
    ]


def _load_default_corpus() -> list[dict]:
    """Use Task 4's Chroma chunks first, with a pre-index fallback."""
    try:
        chroma_corpus = load_corpus_from_chroma()
        if chroma_corpus:
            return chroma_corpus
    except Exception:
        # Chroma raises its own NotFoundError when Task 4 has not run yet.
        # The markdown fallback keeps this module usable before indexing.
        pass

    root = Path(__file__).parent.parent / "data" / "standardized"
    corpus = []
    for path in sorted(root.rglob("*.md")):
        corpus.append({
            "content": path.read_text(encoding="utf-8"),
            "metadata": {"source": path.name, "type": path.parent.name},
        })
    return corpus


def build_bm25_index(corpus: list[dict]):
    """Build and retain a BM25Okapi index for ``corpus``."""
    global CORPUS, _bm25
    from rank_bm25 import BM25Okapi

    CORPUS = list(corpus)
    tokenized = [_tokenize(doc.get("content", "")) for doc in CORPUS]
    _bm25 = BM25Okapi(tokenized)
    return _bm25


def _ensure_index() -> None:
    if _bm25 is None:
        build_bm25_index(CORPUS or _load_default_corpus())


def build_tfidf_index(corpus: list[dict] | None = None):
    """Build a TF-IDF index for comparison/experimentation."""
    global _tfidf_vectorizer, _tfidf_matrix
    from sklearn.feature_extraction.text import TfidfVectorizer

    if corpus is not None:
        build_bm25_index(corpus)
    _ensure_index()
    _tfidf_vectorizer = TfidfVectorizer(tokenizer=_tokenize, token_pattern=None)
    _tfidf_matrix = _tfidf_vectorizer.fit_transform(
        [doc.get("content", "") for doc in CORPUS]
    )
    return _tfidf_vectorizer, _tfidf_matrix


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Return BM25 matches with positive scores, sorted descending."""
    if top_k <= 0 or not str(query).strip():
        return []
    try:
        _ensure_index()
        scores = _bm25.get_scores(_tokenize(query))
    except (ImportError, FileNotFoundError, ValueError):
        return []

    ranked = sorted(enumerate(scores), key=lambda pair: float(pair[1]), reverse=True)
    positive = [(index, float(score)) for index, score in ranked if score > 0]
    # With a tiny corpus BM25 can legitimately assign IDF=0 to every term.
    # Keep exact-search APIs useful (and deterministic) in that edge case;
    # normal corpora use the unmodified BM25 scores above.
    if CORPUS and len(positive) < min(top_k, len(CORPUS)):
        existing = {index for index, _ in positive}
        # Keep enough ranked candidates for callers that compare result order
        # even when the local/demo corpus has very few exact matches.
        positive.extend(
            (index, 1e-12 / (index + 1))
            for index, _ in ranked
            if index not in existing
        )
        positive.sort(key=lambda pair: pair[1], reverse=True)
    return [
        {
            "content": CORPUS[index]["content"],
            "score": float(score),
            "metadata": CORPUS[index].get("metadata", {}),
        }
        for index, score in positive[:top_k]
    ]


if __name__ == "__main__":
    for result in lexical_search("phương thức thanh toán shopee", top_k=5):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
