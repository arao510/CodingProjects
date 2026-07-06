"""
reranker.py
Phase 2: Cross-encoder reranking.

Unlike bi-encoder retrieval (which embeds query and chunks separately),
a cross-encoder takes (query, chunk) pairs and scores them jointly —
much more accurate but too slow to run over the whole corpus.

We use it as a second pass over the top_k_initial retrieved chunks.
"""

from typing import Optional
from rich.console import Console

console = Console()


class CrossEncoderReranker:
    """
    Reranks retrieved chunks using a cross-encoder model.

    The cross-encoder reads both the query and the chunk together,
    allowing it to model interactions between them — superior to
    dot-product similarity but too expensive for full-corpus search.

    Model: cross-encoder/ms-marco-MiniLM-L-6-v2
    - Trained on MS MARCO passage ranking (156k queries)
    - Fast enough for production (< 100ms for 20 candidates on CPU)
    - 6-layer MiniLM — good speed/quality tradeoff
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        console.print(f"[dim]Loading cross-encoder: {model_name}...[/dim]")
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name, max_length=512)
            console.print("[green]✅ Cross-encoder loaded[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠ Cross-encoder unavailable: {e}[/yellow]")
            self.model = None

    def rerank(
        self,
        query: str,
        chunks: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Rerank chunks by cross-encoder relevance score.

        Args:
            query: The user's query
            chunks: List of retrieved chunk dicts (from hybrid retrieval)
            top_k: Number of top chunks to return after reranking

        Returns:
            Top-k chunks sorted by cross-encoder score, each with
            a 'rerank_score' field added.
        """
        if not chunks:
            return []

        if self.model is None:
            # Fallback: return as-is with rrf_score or vector score
            console.print("[yellow]  Using retrieval scores (no cross-encoder)[/yellow]")
            for c in chunks:
                c["rerank_score"] = c.get("rrf_score", c.get("score", 0.0))
            return chunks[:top_k]

        # Build (query, passage) pairs
        pairs = [(query, c["content"]) for c in chunks]

        # Score all pairs at once (batched internally by the library)
        scores = self.model.predict(pairs, show_progress_bar=False)

        # Attach score and sort
        for chunk, score in zip(chunks, scores):
            chunk["rerank_score"] = float(score)

        reranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)

        console.print(
            f"  [dim]Reranker: top score {reranked[0]['rerank_score']:.3f} | "
            f"bottom score {reranked[min(top_k-1, len(reranked)-1)]['rerank_score']:.3f}[/dim]"
        )

        return reranked[:top_k]


if __name__ == "__main__":
    reranker = CrossEncoderReranker()
    test_chunks = [
        {"content": "RAG combines retrieval with neural generation for QA.", "chunk_id": "1", "doc_title": "RAG", "doc_url": ""},
        {"content": "BM25 is a bag-of-words retrieval function.", "chunk_id": "2", "doc_title": "BM25", "doc_url": ""},
        {"content": "Vector search uses embedding similarity.", "chunk_id": "3", "doc_title": "VS", "doc_url": ""},
    ]
    ranked = reranker.rerank("what is RAG?", test_chunks, top_k=2)
    for r in ranked:
        print(f"  [{r['rerank_score']:.3f}] {r['doc_title']}: {r['content'][:60]}")
