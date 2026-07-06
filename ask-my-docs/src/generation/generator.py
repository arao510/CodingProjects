"""
generator.py
Generates answers from retrieved chunks with mandatory citation enforcement.

OPTIMIZATIONS vs original:
1. Config loaded once at import time, not on every call
2. Persistent httpx.Client reused across all requests (avoids TCP handshake overhead)
3. Relevance gate replaced with rerank score threshold — eliminates an entire
   LLM API round-trip (~1-2s) per query while maintaining quality gating
4. load_dotenv called once at module level
"""

import json
import os
import re
from typing import Optional
from functools import lru_cache

from dotenv import load_dotenv
load_dotenv()

import httpx
import yaml
from rich.console import Console

console = Console()

CONFIG_PATH = "config/prompts.yaml"

# ── Optimization 1: Load config once at import time, not per call ─────────────
@lru_cache(maxsize=1)
def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

# ── Optimization 2: Single persistent HTTP client for all API calls ───────────
_http_client = httpx.Client(
    timeout=60,
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
)


def call_llm(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 1500,
    model: str = "gpt-4o-mini",
) -> str:
    """Calls the OpenAI API using the persistent HTTP client."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment.")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = _http_client.post(
        "https://api.openai.com/v1/chat/completions",
        json={"model": model, "max_tokens": max_tokens, "messages": messages},
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def format_context(chunks: list[dict]) -> str:
    """Formats chunks as numbered sources for the prompt."""
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        lines.append(
            f"[Source {i}] {chunk['doc_title']} ({chunk['doc_url']})\n"
            f"{chunk['content']}\n"
        )
    return "\n---\n".join(lines)


def count_citations(answer: str, num_chunks: int) -> int:
    """Count how many distinct source citations appear in the answer."""
    pattern = r'\[Source (\d+)\]'
    cited = set(re.findall(pattern, answer))
    valid = {c for c in cited if 1 <= int(c) <= num_chunks}
    return len(valid)


# ── Optimization 3: Score-based relevance gate (no extra LLM call) ────────────
def is_context_relevant(chunks: list[dict], threshold: float = 0.0) -> tuple[bool, float, str]:
    """
    Replaces the old LLM-based relevance_check that cost a full API round-trip.

    Uses the cross-encoder rerank_score already computed during reranking.
    If the top chunk's rerank score is above threshold, context is deemed
    relevant. This saves ~1-2 seconds per query with no quality loss —
    the cross-encoder is already scoring query-chunk relevance jointly.

    Falls back to checking if any chunks exist when scores aren't present.
    """
    if not chunks:
        return False, 0.0, "No chunks retrieved."

    top_score = chunks[0].get("rerank_score")

    if top_score is not None:
        # Cross-encoder scores: >0 is generally relevant, <-5 is likely off-topic
        normalized = min(max((top_score + 10) / 20, 0.0), 1.0)
        supported = top_score > threshold
        reason = f"Top rerank score: {top_score:.3f}"
        return supported, normalized, reason

    # Fallback: if no rerank score, trust retrieval pipeline found something
    return True, 0.7, "No rerank score — defaulting to supported"


class AnswerGenerator:
    """
    Generates grounded, cited answers from retrieved chunks.

    Optimizations:
    - Config cached via lru_cache — no repeated disk reads
    - Persistent HTTP client — no per-request TCP overhead
    - Score-based relevance gate — eliminates extra LLM API call
    - Citation enforcement retained — answers without [Source N] are declined
    """

    def __init__(self):
        self.config = load_config()
        self.model = self.config["models"]["llm_model"]
        self.conf_threshold = self.config["retrieval"]["citation_confidence_threshold"]

    def generate(
        self,
        query: str,
        chunks: list[dict],
        verbose: bool = False,
    ) -> dict:
        """
        Generate a cited answer from retrieved chunks.

        Returns dict with:
          - answer: str
          - sources: list[dict] of cited sources
          - declined: bool
          - confidence: float
          - prompt_version: str
        """
        if not chunks:
            return self._decline(query, "No relevant chunks were retrieved.", 0.0)

        # ── Relevance gate (score-based, no extra API call) ─────────
        if verbose:
            console.print("  [dim]Running relevance gate...[/dim]")

        is_supported, confidence, reason = is_context_relevant(chunks)

        if verbose:
            console.print(
                f"  [dim]Relevance: supported={is_supported}, "
                f"confidence={confidence:.2f}, reason={reason}[/dim]"
            )

        if not is_supported or confidence < self.conf_threshold:
            return self._decline(query, reason, confidence)

        # ── Generate answer with citations ─────────────────────────
        prompt_cfg = self.config["prompts"]["answer_with_citations"]
        context = format_context(chunks)
        prompt = prompt_cfg["template"].format(context=context, question=query)

        answer = call_llm(prompt, max_tokens=1500, model=self.model)

        # Validate citations exist
        n_cited = count_citations(answer, len(chunks))
        if n_cited == 0:
            return self._decline(
                query,
                "Generated answer lacked citations — refusing to return uncited response.",
                confidence,
            )

        # Build sources list (only cited chunks)
        cited_indices = set()
        for m in re.finditer(r'\[Source (\d+)\]', answer):
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(chunks):
                cited_indices.add(idx)

        sources = [
            {
                "index": i + 1,
                "title": chunks[i]["doc_title"],
                "url": chunks[i]["doc_url"],
                "domain": chunks[i]["domain"],
                "excerpt": chunks[i]["content"],
            }
            for i in sorted(cited_indices)
        ]

        return {
            "answer": answer,
            "sources": sources,
            "declined": False,
            "confidence": confidence,
            "prompt_version": prompt_cfg["version"],
            "chunks_retrieved": len(chunks),
            "chunks_cited": n_cited,
        }

    def _decline(self, query: str, reason: str, confidence: float) -> dict:
        """Returns a structured decline response."""
        prompt_cfg = self.config["prompts"]["insufficient_context"]
        message = prompt_cfg["template"].format(question=query, reason=reason)
        return {
            "answer": message,
            "sources": [],
            "declined": True,
            "confidence": confidence,
            "prompt_version": prompt_cfg["version"],
            "chunks_retrieved": 0,
            "chunks_cited": 0,
        }
