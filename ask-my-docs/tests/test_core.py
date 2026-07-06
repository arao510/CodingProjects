"""
test_core.py
Unit tests for Phase 1 & 2 core logic.
Tests chunker, BM25, hybrid retriever fusion — no API calls.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.ingestion.chunker import chunk_document, count_tokens, split_into_sentences
from src.retrieval.bm25_index import BM25Index, tokenize
from src.retrieval.hybrid_retriever import reciprocal_rank_fusion


# ─────────────────────────────────────────────────────────────────
# CHUNKER TESTS
# ─────────────────────────────────────────────────────────────────

def make_doc(content: str, n: int = 0) -> dict:
    return {
        "id": f"doc{n}",
        "title": f"Test Doc {n}",
        "url": f"http://example.com/{n}",
        "domain": "test",
        "content": content,
    }


def test_chunk_token_counts_in_range():
    """All chunks should be within target range (allowing some slack)."""
    # Generate enough content to produce multiple chunks
    long_content = " ".join([
        f"Sentence {i}: This explains how retrieval augmented generation works in production AI systems."
        for i in range(300)
    ])
    doc = make_doc(long_content)
    chunks = chunk_document(doc, target_tokens=650, overlap_tokens=100, min_tokens=100)

    assert len(chunks) > 1, "Should produce multiple chunks"

    for c in chunks[:-1]:  # last chunk may be smaller
        assert c.token_count <= 800, f"Chunk too large: {c.token_count} tokens"
        assert c.token_count >= 100, f"Chunk too small: {c.token_count} tokens"


def test_chunk_overlap_exists():
    """Consecutive chunks should share some content (overlap)."""
    long_content = " ".join([
        f"Unique sentence number {i} about machine learning and RAG."
        for i in range(200)
    ])
    doc = make_doc(long_content)
    chunks = chunk_document(doc, target_tokens=300, overlap_tokens=80, min_tokens=50)

    assert len(chunks) >= 2, "Need at least 2 chunks to test overlap"

    # The end of chunk N and start of chunk N+1 should share some tokens
    for i in range(len(chunks) - 1):
        end_of_prev = chunks[i].content[-100:]
        start_of_next = chunks[i + 1].content[:100]
        # At least some words should overlap
        prev_words = set(end_of_prev.lower().split())
        next_words = set(start_of_next.lower().split())
        common = prev_words & next_words
        assert len(common) > 0, f"No overlap between chunk {i} and {i+1}"


def test_chunk_indices_sequential():
    """chunk_index should be sequential, total_chunks should be consistent."""
    content = " ".join([f"Sentence {i} about neural networks and embeddings." for i in range(200)])
    doc = make_doc(content)
    chunks = chunk_document(doc)

    for i, c in enumerate(chunks):
        assert c.chunk_index == i
        assert c.total_chunks == len(chunks)


def test_short_doc_single_chunk():
    """A short doc should produce exactly one chunk."""
    doc = make_doc("This is a short document. It has only a few sentences about AI.")
    chunks = chunk_document(doc, target_tokens=650, min_tokens=5)
    assert len(chunks) == 1


def test_empty_doc_no_chunks():
    """Empty content should produce no chunks."""
    doc = make_doc("")
    chunks = chunk_document(doc)
    assert chunks == []


def test_count_tokens():
    assert count_tokens("hello world") == 2
    assert count_tokens("") == 0
    assert count_tokens("a " * 100) in (100, 101)  # trailing space may add a token


# ─────────────────────────────────────────────────────────────────
# BM25 INDEX TESTS
# ─────────────────────────────────────────────────────────────────

SAMPLE_CHUNKS = [
    {"chunk_id": "c1", "content": "RAG systems combine retrieval and generation for question answering.", "doc_title": "RAG", "doc_url": "http://a.com", "domain": "ml", "chunk_index": 0},
    {"chunk_id": "c2", "content": "BM25 is a probabilistic keyword retrieval algorithm based on term frequency.", "doc_title": "IR", "doc_url": "http://b.com", "domain": "ml", "chunk_index": 0},
    {"chunk_id": "c3", "content": "ChromaDB stores vector embeddings and supports cosine similarity search.", "doc_title": "Chroma", "doc_url": "http://c.com", "domain": "ml", "chunk_index": 0},
    {"chunk_id": "c4", "content": "Cross-encoder reranking improves retrieval precision by scoring query-passage pairs jointly.", "doc_title": "Rerank", "doc_url": "http://d.com", "domain": "ml", "chunk_index": 0},
    {"chunk_id": "c5", "content": "Python is a popular programming language for machine learning.", "doc_title": "Python", "doc_url": "http://e.com", "domain": "dev", "chunk_index": 0},
]


def test_bm25_returns_results():
    idx = BM25Index()
    idx.build(SAMPLE_CHUNKS, cache=False)
    results = idx.search("RAG retrieval generation", top_k=3)
    assert len(results) > 0
    assert "bm25_score" in results[0]


def test_bm25_best_match():
    idx = BM25Index()
    idx.build(SAMPLE_CHUNKS, cache=False)
    results = idx.search("BM25 keyword frequency", top_k=5)
    # BM25 result should be top hit
    assert results[0]["chunk_id"] == "c2"


def test_bm25_normalized_scores():
    idx = BM25Index()
    idx.build(SAMPLE_CHUNKS, cache=False)
    results = idx.search("embeddings vector", top_k=5)
    for r in results:
        assert 0.0 <= r["bm25_score"] <= 1.0


def test_tokenizer():
    tokens = tokenize("Hello, World! This is BM25.")
    assert "hello" in tokens
    assert "bm25" in tokens
    assert "," not in tokens


# ─────────────────────────────────────────────────────────────────
# HYBRID FUSION (RRF) TESTS
# ─────────────────────────────────────────────────────────────────

def test_rrf_combines_lists():
    """RRF should return all unique chunks from both lists."""
    list1 = [
        {"chunk_id": "a", "content": "...", "doc_title": "A", "doc_url": ""},
        {"chunk_id": "b", "content": "...", "doc_title": "B", "doc_url": ""},
    ]
    list2 = [
        {"chunk_id": "b", "content": "...", "doc_title": "B", "doc_url": ""},
        {"chunk_id": "c", "content": "...", "doc_title": "C", "doc_url": ""},
    ]
    result = reciprocal_rank_fusion([list1, list2])
    result_ids = {r["chunk_id"] for r in result}
    assert result_ids == {"a", "b", "c"}


def test_rrf_top_ranked_in_both_wins():
    """A chunk top-ranked in both lists should have highest RRF score."""
    shared = {"chunk_id": "top", "content": "...", "doc_title": "Top", "doc_url": ""}
    list1 = [shared, {"chunk_id": "x", "content": ".", "doc_title": "X", "doc_url": ""}]
    list2 = [shared, {"chunk_id": "y", "content": ".", "doc_title": "Y", "doc_url": ""}]

    result = reciprocal_rank_fusion([list1, list2])
    assert result[0]["chunk_id"] == "top"


def test_rrf_scores_attached():
    list1 = [{"chunk_id": "a", "content": ".", "doc_title": "A", "doc_url": ""}]
    list2 = [{"chunk_id": "b", "content": ".", "doc_title": "B", "doc_url": ""}]
    result = reciprocal_rank_fusion([list1, list2])
    for r in result:
        assert "rrf_score" in r
        assert r["rrf_score"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
