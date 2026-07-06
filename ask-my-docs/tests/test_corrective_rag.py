"""
test_corrective_rag.py
Unit tests for Phase 4 Corrective RAG — no API calls.
Tests chunk grading logic, query rewriting fallbacks, and the
corrective loop control flow using mocked LLM and retriever.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import MagicMock, patch


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_chunk(title: str, score: float = 5.0, relevant: bool = True) -> dict:
    return {
        "chunk_id": f"chunk_{title}",
        "content": f"Content about {title} in AWS cloud security.",
        "doc_title": title,
        "doc_url": f"https://aws.amazon.com/{title}",
        "domain": "aws_security",
        "rerank_score": score,
        "chunk_index": 0,
    }


def mock_llm_relevant(prompt, max_tokens=150, model="gpt-4o-mini"):
    """Mock LLM that always grades chunks as relevant."""
    return '{"relevant": true, "score": 0.9, "reason": "Directly answers the question."}'


def mock_llm_irrelevant(prompt, max_tokens=150, model="gpt-4o-mini"):
    """Mock LLM that always grades chunks as irrelevant."""
    return '{"relevant": false, "score": 0.1, "reason": "Does not address the question."}'


def mock_llm_rewrite(prompt, max_tokens=150, model="gpt-4o-mini"):
    """Mock LLM for query rewriting."""
    if "rewrite" in prompt.lower() or "failed" in prompt.lower() or "improved" in prompt.lower():
        return "AWS IAM identity access management best practices security"
    return '{"relevant": true, "score": 0.85, "reason": "Relevant after rewrite."}'


# ── Chunk grading tests ───────────────────────────────────────────────────────

def test_grade_chunk_relevant():
    """Chunk graded as relevant should have grade_relevant=True."""
    from src.corrective.corrective_rag import grade_chunk
    chunk = make_chunk("IAM", score=7.0)
    result = grade_chunk("What is IAM?", chunk, mock_llm_relevant, "gpt-4o-mini")
    assert result["grade_relevant"] is True
    assert result["grade_score"] >= 0.5
    assert "grade_reason" in result


def test_grade_chunk_irrelevant():
    """Chunk graded as irrelevant should have grade_relevant=False."""
    from src.corrective.corrective_rag import grade_chunk
    chunk = make_chunk("S3", score=2.0)
    result = grade_chunk("What is IAM?", chunk, mock_llm_irrelevant, "gpt-4o-mini")
    assert result["grade_relevant"] is False
    assert result["grade_score"] < 0.5


def test_grade_chunk_parse_error_fallback():
    """On LLM parse error, should fall back to rerank score."""
    from src.corrective.corrective_rag import grade_chunk

    def bad_llm(prompt, **kwargs):
        return "not valid json at all {{{"

    chunk = make_chunk("IAM", score=6.0)
    result = grade_chunk("What is IAM?", chunk, bad_llm, "gpt-4o-mini")
    # Should not raise — should use rerank score as fallback
    assert "grade_score" in result
    assert "grade_relevant" in result
    assert result["grade_relevant"] is True  # score 6.0 → rerank > 0 → relevant


def test_grade_chunks_splits_correctly():
    """grade_chunks should correctly split into relevant and irrelevant."""
    from src.corrective.corrective_rag import grade_chunks

    chunks = [make_chunk("IAM"), make_chunk("S3"), make_chunk("VPC")]
    call_count = [0]

    def alternating_llm(prompt, **kwargs):
        call_count[0] += 1
        # First chunk relevant, rest irrelevant
        if call_count[0] == 1:
            return '{"relevant": true, "score": 0.9, "reason": "Good match."}'
        return '{"relevant": false, "score": 0.2, "reason": "Off topic."}'

    relevant, irrelevant = grade_chunks(
        "What is IAM?", chunks, alternating_llm, "gpt-4o-mini", threshold=0.5
    )
    assert len(relevant) + len(irrelevant) == 3
    assert len(relevant) >= 1


def test_grade_chunks_all_relevant():
    """All relevant chunks should land in relevant list."""
    from src.corrective.corrective_rag import grade_chunks
    chunks = [make_chunk(f"doc{i}") for i in range(3)]
    relevant, irrelevant = grade_chunks(
        "security question", chunks, mock_llm_relevant, "gpt-4o-mini", threshold=0.5
    )
    assert len(relevant) == 3
    assert len(irrelevant) == 0


def test_grade_chunks_all_irrelevant():
    """All irrelevant chunks should land in irrelevant list."""
    from src.corrective.corrective_rag import grade_chunks
    chunks = [make_chunk(f"doc{i}") for i in range(3)]
    relevant, irrelevant = grade_chunks(
        "unrelated question", chunks, mock_llm_irrelevant, "gpt-4o-mini", threshold=0.5
    )
    assert len(relevant) == 0
    assert len(irrelevant) == 3


# ── Query rewriting tests ─────────────────────────────────────────────────────

def test_rewrite_query_returns_string():
    """rewrite_query should always return a non-empty string."""
    from src.corrective.corrective_rag import rewrite_query
    result = rewrite_query(
        "What is IAM?",
        "No relevant chunks found.",
        mock_llm_rewrite,
        "gpt-4o-mini",
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_rewrite_query_fallback_on_error():
    """On LLM error, rewrite_query should return the original query."""
    from src.corrective.corrective_rag import rewrite_query

    def error_llm(prompt, **kwargs):
        raise RuntimeError("API error")

    original = "What is AWS IAM?"
    result = rewrite_query(original, "failed", error_llm, "gpt-4o-mini")
    assert result == original


def test_rewrite_query_strips_quotes():
    """rewrite_query should strip wrapping quotes from LLM output."""
    from src.corrective.corrective_rag import rewrite_query

    def quoted_llm(prompt, **kwargs):
        return '"AWS IAM identity and access management"'

    result = rewrite_query("IAM?", "failed", quoted_llm, "gpt-4o-mini")
    assert not result.startswith('"')
    assert not result.endswith('"')


# ── CorrectiveRAG loop tests ─────────────────────────────────────────────────

def make_corrective_rag(min_good_chunks=2, max_retries=1):
    """Build a CorrectiveRAG instance with mocked dependencies."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [make_chunk(f"retry_{i}") for i in range(5)]

    mock_reranker = MagicMock()
    mock_reranker.rerank.return_value = [make_chunk(f"reranked_{i}") for i in range(5)]

    mock_generator = MagicMock()
    mock_generator.generate.return_value = {
        "answer": "This is the answer [Source 1].",
        "sources": [{"index": 1, "title": "IAM", "url": "http://aws.com", "domain": "aws_security", "excerpt": "..."}],
        "declined": False,
        "confidence": 0.9,
        "prompt_version": "1.0.0",
        "chunks_retrieved": 5,
        "chunks_cited": 1,
    }
    mock_generator._decline.return_value = {
        "answer": "Cannot answer.",
        "sources": [],
        "declined": True,
        "confidence": 0.0,
        "prompt_version": "1.0.0",
        "chunks_retrieved": 0,
        "chunks_cited": 0,
    }

    with patch("src.corrective.corrective_rag.load_config") as mock_cfg:
        mock_cfg.return_value = {
            "retrieval": {
                "corrective_rag": {
                    "enabled": True,
                    "chunk_relevance_threshold": 0.5,
                    "min_good_chunks": min_good_chunks,
                    "max_retries": max_retries,
                },
                "top_k_initial": 20,
                "top_k_final": 5,
            },
            "models": {"llm_model": "gpt-4o-mini"},
            "prompts": {
                "chunk_relevance_grader": {"template": "Grade: {question} {chunk}"},
                "query_rewriter": {"template": "Rewrite: {query} {reason}"},
                "insufficient_context": {"template": "Cannot answer: {question} {reason}", "version": "1.0.0"},
            },
        }

        from src.corrective.corrective_rag import CorrectiveRAG
        with patch("src.generation.generator.call_llm", mock_llm_relevant):
            crag = CorrectiveRAG(mock_retriever, mock_reranker, mock_generator)
            crag._call_llm = mock_llm_relevant
            return crag, mock_generator


def test_corrective_rag_passes_with_good_chunks():
    """When enough chunks are relevant, should generate without retrying."""
    crag, mock_gen = make_corrective_rag(min_good_chunks=2)
    chunks = [make_chunk(f"doc{i}", score=7.0) for i in range(5)]

    with patch("src.corrective.corrective_rag.grade_chunks") as mock_grade:
        mock_grade.return_value = (chunks[:3], chunks[3:])  # 3 relevant
        result = crag.run("What is IAM?", chunks)

    assert result["declined"] is False
    assert "corrective_rag" in result
    assert result["corrective_rag"]["chunks_kept"] == 3
    assert result["corrective_rag"]["retries"] == 0
    assert result["corrective_rag"]["query_rewritten"] is False


def test_corrective_rag_declines_when_no_good_chunks():
    """When no chunks are relevant after all retries, should decline."""
    crag, mock_gen = make_corrective_rag(min_good_chunks=2, max_retries=1)
    chunks = [make_chunk(f"doc{i}", score=7.0) for i in range(5)]

    with patch("src.corrective.corrective_rag.grade_chunks") as mock_grade, \
         patch("src.corrective.corrective_rag.rewrite_query") as mock_rewrite:
        mock_grade.return_value = ([], chunks)   # always 0 relevant
        mock_rewrite.return_value = "rewritten query"
        result = crag.run("What is IAM?", chunks)

    assert result["declined"] is True
    assert result["corrective_rag"]["query_rewritten"] is True


def test_corrective_rag_metadata_attached():
    """Result should always have corrective_rag metadata dict."""
    crag, _ = make_corrective_rag()
    chunks = [make_chunk("IAM", score=8.0) for _ in range(5)]

    with patch("src.corrective.corrective_rag.grade_chunks") as mock_grade:
        mock_grade.return_value = (chunks, [])
        result = crag.run("What is IAM?", chunks)

    assert "corrective_rag" in result
    meta = result["corrective_rag"]
    assert "chunks_graded" in meta
    assert "chunks_kept" in meta
    assert "chunks_filtered" in meta
    assert "retries" in meta
    assert "query_rewritten" in meta


def test_corrective_rag_disabled_passthrough():
    """When corrective RAG is disabled, should pass chunks straight to generator."""
    crag, mock_gen = make_corrective_rag()
    crag.enabled = False
    chunks = [make_chunk("IAM")]

    crag.run("What is IAM?", chunks)
    mock_gen.generate.assert_called_once_with("What is IAM?", chunks, verbose=False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
