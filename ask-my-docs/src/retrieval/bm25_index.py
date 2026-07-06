"""
bm25_index.py
BM25 keyword search index built from corpus chunks.
Complements vector search in hybrid retrieval (Phase 2).
"""

import re
import pickle
from pathlib import Path
from typing import Optional

from rank_bm25 import BM25Okapi
from rich.console import Console

console = Console()

BM25_CACHE_PATH = ".bm25_index.pkl"


def tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenizer for BM25."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)  # remove punctuation
    tokens = text.split()
    # Remove very short tokens
    return [t for t in tokens if len(t) > 1]


class BM25Index:
    """
    BM25Okapi index over all corpus chunks.
    Supports keyword search and score retrieval for hybrid fusion.
    """

    def __init__(self):
        self.bm25: Optional[BM25Okapi] = None
        self.chunks: list[dict] = []  # parallel list of chunk dicts

    def build(self, chunks: list[dict], cache: bool = True) -> None:
        """
        Build BM25 index from a list of chunk dicts.
        Each chunk dict must have 'content' and metadata fields.
        """
        console.print(f"[cyan]Building BM25 index over {len(chunks)} chunks...[/cyan]")

        self.chunks = chunks
        tokenized = [tokenize(c["content"]) for c in chunks]
        self.bm25 = BM25Okapi(tokenized)

        if cache:
            with open(BM25_CACHE_PATH, "wb") as f:
                pickle.dump({"bm25": self.bm25, "chunks": self.chunks}, f)

        console.print(f"[green]✅ BM25 index built ({len(chunks)} docs)[/green]")

    def load(self, cache_path: str = BM25_CACHE_PATH) -> bool:
        """Load index from cache. Returns True if successful."""
        path = Path(cache_path)
        if not path.exists():
            return False
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.bm25 = data["bm25"]
        self.chunks = data["chunks"]
        console.print(f"[dim]Loaded BM25 index ({len(self.chunks)} chunks from cache)[/dim]")
        return True

    def search(self, query: str, top_k: int = 20) -> list[dict]:
        """
        BM25 search. Returns top_k results with normalized scores.
        """
        if self.bm25 is None:
            raise RuntimeError("BM25 index not built. Call build() first.")

        query_tokens = tokenize(query)
        raw_scores = self.bm25.get_scores(query_tokens)

        # Normalize scores to [0, 1]
        max_score = max(raw_scores) if max(raw_scores) > 0 else 1.0
        norm_scores = raw_scores / max_score

        # Get top_k indices
        top_indices = sorted(
            range(len(norm_scores)), key=lambda i: norm_scores[i], reverse=True
        )[:top_k]

        results = []
        for idx in top_indices:
            if norm_scores[idx] == 0:
                continue  # skip zero-score results
            chunk = self.chunks[idx].copy()
            chunk["bm25_score"] = float(norm_scores[idx])
            results.append(chunk)

        return results


if __name__ == "__main__":
    # Smoke test
    idx = BM25Index()
    test_chunks = [
        {"content": "RAG systems combine retrieval with generation", "doc_title": "RAG", "doc_url": ""},
        {"content": "BM25 is a keyword based retrieval algorithm", "doc_title": "BM25", "doc_url": ""},
        {"content": "ChromaDB stores vector embeddings for semantic search", "doc_title": "Chroma", "doc_url": ""},
    ]
    idx.build(test_chunks, cache=False)
    results = idx.search("vector embeddings")
    for r in results:
        print(f"  [{r['bm25_score']:.3f}] {r['doc_title']}: {r['content'][:60]}")
