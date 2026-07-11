"""
kg/baseline.py — the strawman: plain BM25 keyword search over document
title + content. No ownership, no permissions, no relationships — exactly
what a document search tool sees.
"""

import re

from rank_bm25 import BM25Okapi

from kg.data import DOCUMENTS


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class BaselineSearch:
    """BM25 index over the same corpus the graph holds."""

    def __init__(self):
        self.docs = DOCUMENTS
        corpus = [_tokenize(f"{d['title']} {d['content']}") for d in self.docs]
        self.bm25 = BM25Okapi(corpus)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        scores = self.bm25.get_scores(_tokenize(query))
        ranked = sorted(zip(self.docs, scores), key=lambda x: x[1], reverse=True)
        return [
            {
                "id": d["id"],
                "title": d["title"],
                "type": d["type"],
                "classification": d["classification"],
                "owner_team_id": d["team_id"],
                "score": round(float(score), 2),
            }
            for d, score in ranked[:top_k]
            if score > 0
        ]
