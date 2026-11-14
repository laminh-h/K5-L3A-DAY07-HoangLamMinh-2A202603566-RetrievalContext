"""Retrieval methods over the same Day 6 corpus (index A, 618 chunks).

dense   : Day 6 embedder + Day 6 Chroma collection (live query, cosine, HNSW), metadata pre-filter.
bm25    : Okapi BM25 over the exported chunk text (number-aware tokenizer), same metadata filter.
hybrid  : Reciprocal Rank Fusion of dense and bm25 rankings (no raw-score addition).
rerank  : hybrid candidates re-scored by a cross-encoder; returns cross-encoder order.

Every result: id, text, source_id, source, page, metadata, score, rank, method.
Errors (model/store) propagate - there is no silent fallback to fake results.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from . import config

ALLOWED_FILTER_KEYS = {"edition", "year", "section", "source_id", "language"}
TOKEN_RE = re.compile(r"\d+(?:[.,]\d+)*|[^\W\d_]+", re.UNICODE)
STOP = set("""a an the of in on at to for from by with and or is are was were be been being as that this
these those it its into than then which what who whom how when where why do does did has have had
not no but if so such about over under up down out more most less much very can could would should
will may might""".split())


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.casefold()) if t not in STOP]


def _passes(chunk: dict[str, Any], filters: dict[str, Any] | None) -> bool:
    if not filters:
        return True
    unknown = set(filters) - ALLOWED_FILTER_KEYS
    if unknown:
        raise ValueError(f"filter key không được phép: {sorted(unknown)}")
    for k, v in filters.items():
        have = chunk["source_id"] if k == "source_id" else chunk["metadata"].get(k)
        if have != v:
            return False
    return True


def _result(chunk: dict[str, Any], score: float, rank: int, method: str) -> dict[str, Any]:
    return {"id": chunk["id"], "text": chunk["text"], "source_id": chunk["source_id"],
            "source": chunk["source"], "page": chunk["page"], "metadata": chunk["metadata"],
            "score": round(float(score), 6), "rank": rank, "method": method}


class DenseRetriever:
    """Queries the persisted Day 6 Chroma collection with the Day 6 embedding model."""
    name = "dense"

    def __init__(self, chunks: list[dict[str, Any]]):
        from src.embeddings import SentenceTransformerEmbedder  # Day 6 code
        from src.store import ChromaStore

        self.by_id = {c["id"]: c for c in chunks}
        self.embedder = SentenceTransformerEmbedder(config.EMBEDDING_MODEL)
        self.store = ChromaStore(config.CHROMA_PATH, self.embedder.dimensions, self.embedder.model_name)
        n = self.store.count(config.DAY6_INDEX)
        if n != len(chunks):
            raise RuntimeError(f"Chroma index {config.DAY6_INDEX} has {n} chunks, export has {len(chunks)}; re-run export")

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        where = None
        if filters:
            where = {("document_id" if k == "source_id" else k): v for k, v in filters.items()}
        hits = self.store.search(config.DAY6_INDEX, self.embedder.embed_query(query), top_k=top_k, filters=where)
        return [_result(self.by_id[h["chunk_id"]], h["score"], i, self.name) for i, h in enumerate(hits, 1)]


class BM25Retriever:
    name = "bm25"

    def __init__(self, chunks: list[dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.chunks, self.k1, self.b = chunks, k1, b
        self.tf = [Counter(tokenize(c["text"])) for c in chunks]
        self.len = [sum(t.values()) for t in self.tf]
        self.avg = sum(self.len) / len(self.len)
        df = Counter(term for t in self.tf for term in t)
        n = len(chunks)
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        out = []
        for tf, dl in zip(self.tf, self.len):
            s = 0.0
            for t in q:
                f = tf.get(t)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avg))
            out.append(s)
        return out

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        _passes(self.chunks[0], filters)  # validates filter keys even when nothing scores
        scored = [(s, c) for s, c in zip(self.scores(query), self.chunks) if s > 0 and _passes(c, filters)]
        scored.sort(key=lambda x: -x[0])
        return [_result(c, s, i, self.name) for i, (s, c) in enumerate(scored[:top_k], 1)]


class HybridRRF:
    """score(d) = sum_r 1 / (k + rank_r(d)) over dense and bm25 candidate lists."""
    name = "hybrid"

    def __init__(self, dense: DenseRetriever, bm25: BM25Retriever, k: int = 60, candidates: int = 50):
        self.dense, self.bm25, self.k, self.candidates = dense, bm25, k, candidates

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        fused: dict[str, float] = {}
        keep: dict[str, dict[str, Any]] = {}
        for r in (self.dense, self.bm25):
            for h in r.search(query, filters=filters, top_k=self.candidates):
                fused[h["id"]] = fused.get(h["id"], 0.0) + 1.0 / (self.k + h["rank"])
                keep[h["id"]] = h
        order = sorted(fused, key=lambda i: -fused[i])[:top_k]
        return [_result(keep[i], fused[i], n, self.name) for n, i in enumerate(order, 1)]


class Reranked:
    """Cross-encoder rerank of the first-stage candidates (query, chunk) pairs."""

    def __init__(self, first: Any, candidates: int = 20, model_name: str | None = None):
        from sentence_transformers import CrossEncoder

        self.first, self.candidates = first, candidates
        self.model_name = model_name or config.RERANK_MODEL
        self.model = CrossEncoder(self.model_name, device="cpu")
        self.name = f"{first.name}+rerank"

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        cands = self.first.search(query, filters=filters, top_k=self.candidates)
        if not cands:
            return []
        scores = self.model.predict([(query, c["text"]) for c in cands], show_progress_bar=False)
        order = sorted(zip(scores, cands), key=lambda x: -x[0])[:top_k]
        return [_result(c, s, n, self.name) for n, (s, c) in enumerate(order, 1)]


def neighbors(chunk_id: str, by_id: dict[str, dict[str, Any]], window: int = 1) -> list[dict[str, Any]]:
    """Adjacent chunks on the same page (Day 6 IDs end with :cNN). Used for context expansion."""
    prefix, _, idx = chunk_id.rpartition(":c")
    out = []
    for d in range(-window, window + 1):
        if d == 0:
            continue
        nid = f"{prefix}:c{int(idx) + d:02d}"
        if nid in by_id:
            out.append(by_id[nid])
    return out


def build(method: str, chunks: list[dict[str, Any]], cache: dict[str, Any] | None = None) -> Any:
    """Factory with a cache so models load once per process."""
    cache = cache if cache is not None else {}
    if "dense" not in cache and method in ("dense", "hybrid", "hybrid+rerank", "dense+rerank"):
        cache["dense"] = DenseRetriever(chunks)
    if "bm25" not in cache and method in ("bm25", "hybrid", "hybrid+rerank"):
        cache["bm25"] = BM25Retriever(chunks)
    if method in ("hybrid", "hybrid+rerank") and "hybrid" not in cache:
        cache["hybrid"] = HybridRRF(cache["dense"], cache["bm25"])
    if method == "hybrid+rerank" and method not in cache:
        cache[method] = Reranked(cache["hybrid"])
    if method == "dense+rerank" and method not in cache:
        cache[method] = Reranked(cache["dense"])
    if method not in cache:
        raise ValueError(f"unknown method {method}")
    return cache[method]
