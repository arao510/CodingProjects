"""
corrective_rag.py
Phase 4: Corrective RAG

The core idea: instead of treating all retrieved chunks as equally useful
(and declining if the batch as a whole seems weak), we:

1. GRADE each chunk individually — relevant or irrelevant?
2. FILTER — keep only relevant chunks
3. CORRECT — if too few good chunks remain, rewrite the query and retry once
4. GENERATE — answer from the filtered, high-quality chunk set

This directly addresses the declined questions from Phase 3 eval,
where some chunks were good but others dragged down the batch score.

Flow:
    chunks (from reranker)
        │
        ▼
    grade_chunks()  ──► relevant_chunks + irrelevant_chunks
        │
        ├─ enough good chunks? ──► generate answer
        │
        └─ too few good chunks?
               │
               ▼
           rewrite_query()
               │
               ▼
           re-retrieve + rerank
               │
               ▼
           grade_chunks() again
               │
               ├─ now enough? ──► generate answer
               └─ still not enough? ──► decline with clear reason
"""

import json
import re
import concurrent.futures
from functools import lru_cache

import yaml
from rich.console import Console

console = Console()
CONFIG_PATH = "config/prompts.yaml"


@lru_cache(maxsize=1)
def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def grade_chunk(
    question: str,
    chunk: dict,
    call_llm_fn,
    model: str,
) -> dict:
    """
    Grades a single chunk for relevance to the question.
    Returns the chunk with added grade_score, grade_relevant, grade_reason fields.
    """
    config = load_config()
    prompt_template = config["prompts"]["chunk_relevance_grader"]["template"]
    prompt = prompt_template.format(
        question=question,
        chunk=chunk["content"][:1500],  # cap to avoid token bloat
    )

    try:
        raw = call_llm_fn(prompt, max_tokens=150, model=model)
        raw = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)
        chunk = chunk.copy()
        chunk["grade_score"] = float(result.get("score", 0.5))
        chunk["grade_relevant"] = bool(result.get("relevant", False))
        chunk["grade_reason"] = result.get("reason", "")
        return chunk
    except Exception as e:
        # On parse error, fall back to rerank score
        chunk = chunk.copy()
        rerank = chunk.get("rerank_score", 0)
        chunk["grade_score"] = min(max((rerank + 10) / 20, 0.0), 1.0)
        chunk["grade_relevant"] = rerank > 0
        chunk["grade_reason"] = f"Grade parse error — using rerank score fallback"
        return chunk


def grade_chunks(
    question: str,
    chunks: list[dict],
    call_llm_fn,
    model: str,
    threshold: float = 0.5,
    verbose: bool = False,
) -> tuple[list[dict], list[dict]]:
    """
    Grades all chunks in parallel and splits into relevant/irrelevant.
    Parallel grading keeps latency close to a single LLM call.
    Returns (relevant_chunks, irrelevant_chunks).
    """
    # Grade all chunks concurrently — each is independent
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(grade_chunk, question, chunk, call_llm_fn, model): i
            for i, chunk in enumerate(chunks)
        }
        graded_with_index = []
        for future, idx in futures.items():
            graded_with_index.append((idx, future.result()))

    # Restore original order
    graded_with_index.sort(key=lambda x: x[0])
    graded = [chunk for _, chunk in graded_with_index]

    relevant = [c for c in graded if c["grade_relevant"] and c["grade_score"] >= threshold]
    irrelevant = [c for c in graded if not c["grade_relevant"] or c["grade_score"] < threshold]

    if verbose:
        console.print(
            f"  [dim]Chunk grading: {len(relevant)} relevant, "
            f"{len(irrelevant)} irrelevant (threshold={threshold})[/dim]"
        )
        for c in graded:
            icon = "✅" if c["grade_relevant"] else "❌"
            score = c.get("grade_score", 0)
            title = c.get("doc_title", "?")[:35]
            reason = c.get("grade_reason", "")[:55]
            console.print(f"  [dim]  {icon} [{score:.2f}] {title} — {reason}[/dim]")

    return relevant, irrelevant


def rewrite_query(
    original_query: str,
    reason: str,
    call_llm_fn,
    model: str,
) -> str:
    """
    Rewrites a failed query using the LLM to improve retrieval.
    Produces better search terminology when initial retrieval is poor.
    """
    config = load_config()
    prompt_template = config["prompts"]["query_rewriter"]["template"]
    prompt = prompt_template.format(query=original_query, reason=reason)

    try:
        rewritten = call_llm_fn(prompt, max_tokens=100, model=model).strip()
        rewritten = rewritten.strip('"\'')  # strip if model wraps in quotes
        return rewritten if rewritten else original_query
    except Exception:
        return original_query  # fallback: keep original


class CorrectiveRAG:
    """
    Phase 4: Corrective RAG wrapper.

    Sits between the reranker and the generator. Takes reranked chunks,
    grades them individually, filters bad ones, retries with a rewritten
    query if needed, then generates from the best available context.

    This directly improves on the Phase 3 pipeline which could only
    accept or reject the entire batch — now we can salvage partial
    retrieval results and recover from poor initial queries.
    """

    def __init__(self, hybrid_retriever, reranker, generator):
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker
        self.generator = generator

        config = load_config()
        crag_cfg = config["retrieval"]["corrective_rag"]
        self.enabled = crag_cfg["enabled"]
        self.chunk_threshold = crag_cfg["chunk_relevance_threshold"]
        self.min_good_chunks = crag_cfg["min_good_chunks"]
        self.max_retries = crag_cfg["max_retries"]

        self.model = config["models"]["llm_model"]
        self.top_k_initial = config["retrieval"]["top_k_initial"]
        self.top_k_final = config["retrieval"]["top_k_final"]

        # Import here to avoid circular imports
        from src.generation.generator import call_llm
        self._call_llm = call_llm

    def run(
        self,
        question: str,
        initial_chunks: list[dict],
        verbose: bool = False,
    ) -> dict:
        """
        Corrective RAG loop:
        1. Grade initial reranked chunks individually
        2. Enough good chunks → generate answer immediately
        3. Too few → rewrite query, re-retrieve, re-grade (up to max_retries)
        4. Still not enough → decline with a detailed explanation
        """
        if not self.enabled:
            # Corrective RAG disabled — pass through directly
            return self.generator.generate(question, initial_chunks, verbose=verbose)

        attempt = 0
        current_query = question
        current_chunks = initial_chunks
        relevant = []
        irrelevant = []

        while attempt <= self.max_retries:
            if verbose and attempt > 0:
                console.print(
                    f"\n[yellow]  ↻ Corrective retry {attempt}/{self.max_retries} "
                    f"with rewritten query: \"{current_query}\"[/yellow]"
                )

            # ── Step 1: Grade each chunk individually ──────────────
            if verbose:
                console.print(f"\n[cyan]  Corrective RAG: grading {len(current_chunks)} chunks...[/cyan]")

            relevant, irrelevant = grade_chunks(
                question=question,       # always grade vs ORIGINAL question
                chunks=current_chunks,
                call_llm_fn=self._call_llm,
                model=self.model,
                threshold=self.chunk_threshold,
                verbose=verbose,
            )

            # ── Step 2: Enough good chunks → generate ──────────────
            if len(relevant) >= self.min_good_chunks:
                if verbose:
                    console.print(
                        f"  [green]  ✅ {len(relevant)} relevant chunks — generating answer[/green]"
                    )
                result = self.generator.generate(question, relevant, verbose=verbose)
                result["corrective_rag"] = {
                    "enabled": True,
                    "chunks_graded": len(current_chunks),
                    "chunks_kept": len(relevant),
                    "chunks_filtered": len(irrelevant),
                    "retries": attempt,
                    "query_rewritten": attempt > 0,
                    "rewritten_query": current_query if attempt > 0 else None,
                }
                return result

            # ── Step 3: Not enough — rewrite query if retries left ─
            if attempt >= self.max_retries:
                break

            rewrite_reason = (
                f"Only {len(relevant)} of {len(current_chunks)} chunks were relevant. "
                + (
                    f"Top irrelevant reason: {irrelevant[0].get('grade_reason', 'unclear')}"
                    if irrelevant else ""
                )
            )

            if verbose:
                console.print(
                    f"  [yellow]  ⚠ Only {len(relevant)} good chunks "
                    f"(need {self.min_good_chunks}). Rewriting query...[/yellow]"
                )

            current_query = rewrite_query(
                original_query=question,
                reason=rewrite_reason,
                call_llm_fn=self._call_llm,
                model=self.model,
            )

            if verbose:
                console.print(f"  [cyan]  New query: \"{current_query}\"[/cyan]")

            # Re-retrieve with new query, rerank against original question
            new_candidates = self.hybrid_retriever.retrieve(
                current_query, top_k=self.top_k_initial, verbose=False
            )
            current_chunks = self.reranker.rerank(
                question,   # rerank against ORIGINAL question for quality
                new_candidates,
                top_k=self.top_k_final,
            )

            attempt += 1

        # ── Step 4: All retries exhausted — decline ────────────────
        parts = []
        if relevant:
            parts.append(
                f"Only {len(relevant)} relevant chunk(s) found after "
                f"{attempt} attempt(s) (minimum needed: {self.min_good_chunks})."
            )
        else:
            parts.append("No relevant chunks found after retrieval and correction.")
        if attempt > 0:
            parts.append(f"Query was rewritten to: \"{current_query}\"")

        if verbose:
            console.print(f"  [red]  ✗ Corrective RAG exhausted — declining[/red]")

        result = self.generator._decline(question, " ".join(parts), 0.0)
        result["corrective_rag"] = {
            "enabled": True,
            "chunks_graded": len(current_chunks),
            "chunks_kept": len(relevant),
            "chunks_filtered": len(irrelevant),
            "retries": attempt,
            "query_rewritten": attempt > 0,
            "rewritten_query": current_query if attempt > 0 else None,
        }
        return result
