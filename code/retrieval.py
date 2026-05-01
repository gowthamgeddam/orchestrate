"""
BM25-based retrieval over the support corpus.
"""

import re
from rank_bm25 import BM25Okapi

from corpus import Document


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class Retriever:
    def __init__(self, docs: list[Document]):
        self._docs = docs
        corpus_tokens = [_tokenize(f"{d.title} {d.content}") for d in docs]
        self._bm25 = BM25Okapi(corpus_tokens)

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        tokens = _tokenize(query)
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self._docs[i] for i in ranked[:top_k]]
