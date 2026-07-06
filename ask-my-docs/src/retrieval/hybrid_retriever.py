"""
hybrid_retriever.py
Phase 2: Hybrid retrieval — combines BM25 keyword search with
vector semantic search using Reciprocal Rank Fusion (RRF).

OPTIMIZATION: BM25 and vector search now run in parallel threads,
cutting retrieval latency roughly in half.
"""

import concurrent.futures
from rich.console import Console

console = Console()


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    id_field: str = "chunk_id",
    k: int = 60,
) -> list[dict]:
    """
    Reciprocal Rank Fusion: merges multiple ranked lists into one.
    RRF score = sum(1 / (k + rank_i)) for each list.
    """
    fusion_scores: dict[str, float] = {}
    chunk_registry: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list, start=1):
            cid = chunk[id_field]
            fusion_scores[cid] = fusion_scores.get(cid, 0.0) + 1.0 / (k + rank)
            if cid not in chunk_registry:
                chunk_registry[cid] = chunk

    sorted_ids = sorted(fusion_scores, key=lambda cid: fusion_scores[cid], reverse=True)

    results = []
    for cid in sorted_ids:
        chunk = chunk_registry[cid].copy()
        chunk["rrf_score"] = fusion_scores[cid]
        results.append(chunk)

    return results


class HybridRetriever:
    """
    Phase 2 retriever: BM25 + Vector → RRF fusion → top candidates.

    OPTIMIZATION: BM25 and vector search run concurrently in a
    ThreadPoolExecutor, reducing retrieval from ~2x latency to ~1x.
    """

    def __init__(
        self,
        vector_store,
        bm25_index,
        top_k_initial: int = 20,
    ):
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.top_k_initial = top_k_initial
        # Reuse executor across queries — avoids thread spawn overhead
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    def retrieve(
        self,
        query: str,
        top_k: int = 20,
        verbose: bool = False,
    ) -> list[dict]:
        """
        Hybrid retrieval with parallel BM25 + vector search.
        """
        # ── Submit both searches simultaneously ─────────────────────
        vec_future = self._executor.submit(
            self.vector_store.search, query, self.top_k_initial
        )
        bm25_future = self._executor.submit(
            self.bm25_index.search, query, self.top_k_initial
        )

        # ── Collect results (blocks until both complete) ────────────
        vector_hits = vec_future.result()
        bm25_hits = bm25_future.result()

        # Ensure chunk_id fields are present
        for i, hit in enumerate(vector_hits):
            if "chunk_id" not in hit:
                hit["chunk_id"] = f"vec_{i}_{hit.get('doc_title', '')}_{hit.get('chunk_index', i)}"

        for i, hit in enumerate(bm25_hits):
            if "chunk_id" not in hit:
                hit["chunk_id"] = f"bm25_{hit.get('doc_title', '')}_{hit.get('chunk_index', i)}"

        if verbose:
            console.print(
                f"  [dim]Vector: {len(vector_hits)} hits | BM25: {len(bm25_hits)} hits[/dim]"
            )

        # ── RRF fusion ───────────────────────────────────────────────
        fused = reciprocal_rank_fusion([vector_hits, bm25_hits])

        # Annotate retrieval source
        vec_ids = {h["chunk_id"] for h in vector_hits}
        bm_ids  = {h["chunk_id"] for h in bm25_hits}
        for chunk in fused:
            cid = chunk["chunk_id"]
            in_vec = cid in vec_ids
            in_bm  = cid in bm_ids
            if in_vec and in_bm:
                chunk["retrieval_source"] = "both"
            elif in_vec:
                chunk["retrieval_source"] = "vector"
            else:
                chunk["retrieval_source"] = "bm25"

        if verbose:
            console.print(f"  [dim]After RRF fusion: {len(fused)} unique chunks[/dim]")

        return fused[:top_k]

    def __del__(self):
        self._executor.shutdown(wait=False)
