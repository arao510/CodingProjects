"""
pipeline.py
Main RAG pipeline — Phase 4: Corrective RAG.

Full flow:
  query
    → cache check
    → hybrid retrieval (parallel BM25 + vector + RRF)
    → cross-encoder reranking
    → corrective RAG (grade chunks → filter → rewrite & retry if needed)
    → citation-enforced generation
"""

import hashlib
from collections import OrderedDict

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
CONFIG_PATH = "config/prompts.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


class QueryCache:
    """LRU cache for query results."""
    def __init__(self, max_size: int = 100):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size

    def _key(self, query: str) -> str:
        return hashlib.md5(query.lower().strip().encode()).hexdigest()

    def get(self, query: str) -> dict | None:
        key = self._key(query)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, query: str, result: dict):
        key = self._key(query)
        self._cache[key] = result
        self._cache.move_to_end(key)
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self):
        self._cache.clear()

    def size(self) -> int:
        return len(self._cache)


class RAGPipeline:
    """
    Phase 4 RAG Pipeline.

    Phases:
      1 — Vector store (ChromaDB) + chunking
      2 — Hybrid retrieval (BM25 + vector + RRF) + cross-encoder reranking
          + citation enforcement
      3 — RAGAS faithfulness evaluation + CI gate
      4 — Corrective RAG: chunk-level grading + query rewriting + retry
    """

    def __init__(self, lazy_load: bool = False, cache_size: int = 100):
        self.config = load_config()
        cfg = self.config["retrieval"]
        model_cfg = self.config["models"]

        self.top_k_initial = cfg["top_k_initial"]
        self.top_k_final = cfg["top_k_final"]
        self._cache = QueryCache(max_size=cache_size)

        if lazy_load:
            return

        from src.retrieval.vector_store import VectorStore
        self.vector_store = VectorStore(model_name=model_cfg["embedding"])

        from src.retrieval.bm25_index import BM25Index
        self.bm25_index = BM25Index()
        if not self.bm25_index.load():
            console.print("[yellow]BM25 index not found — run ingest first.[/yellow]")

        from src.retrieval.hybrid_retriever import HybridRetriever
        self.hybrid_retriever = HybridRetriever(
            vector_store=self.vector_store,
            bm25_index=self.bm25_index,
            top_k_initial=self.top_k_initial,
        )

        from src.reranking.reranker import CrossEncoderReranker
        self.reranker = CrossEncoderReranker(model_name=model_cfg["reranker"])

        from src.generation.generator import AnswerGenerator
        self.generator = AnswerGenerator()

        # Phase 4: Corrective RAG
        from src.corrective.corrective_rag import CorrectiveRAG
        self.corrective_rag = CorrectiveRAG(
            hybrid_retriever=self.hybrid_retriever,
            reranker=self.reranker,
            generator=self.generator,
        )

        console.print("[bold green]✅ RAG Pipeline ready (Phase 4: Corrective RAG)[/bold green]")

    def query(self, question: str, verbose: bool = True) -> dict:
        """
        Full pipeline:
          question → cache → hybrid retrieve → rerank →
          corrective RAG (grade + filter + rewrite) → generate → cite
        """
        if verbose:
            console.print(Panel(f"[bold]Query:[/bold] {question}", style="blue"))

        # ── Cache check ────────────────────────────────────────────
        cached = self._cache.get(question)
        if cached:
            if verbose:
                console.print("[dim]⚡ Cache hit — returning cached result[/dim]")
                self._print_result(cached)
            return cached

        # ── Step 1: Hybrid retrieval ────────────────────────────────
        if verbose:
            console.print("\n[cyan]Step 1: Hybrid retrieval...[/cyan]")

        candidates = self.hybrid_retriever.retrieve(
            question, top_k=self.top_k_initial, verbose=verbose
        )

        if verbose:
            console.print(f"  Retrieved {len(candidates)} candidates")
            for c in candidates[:3]:
                src = c.get("retrieval_source", "?")
                score = c.get("rrf_score", 0)
                console.print(f"  [dim][{src}] {c['doc_title']} | rrf={score:.4f}[/dim]")

        # ── Step 2: Cross-encoder reranking ────────────────────────
        if verbose:
            console.print(
                f"\n[cyan]Step 2: Reranking top {self.top_k_initial} → {self.top_k_final}...[/cyan]"
            )

        reranked = self.reranker.rerank(question, candidates, top_k=self.top_k_final)

        # ── Step 3: Corrective RAG (grade → filter → rewrite → retry)
        if verbose:
            console.print("\n[cyan]Step 3: Corrective RAG...[/cyan]")

        result = self.corrective_rag.run(question, reranked, verbose=verbose)

        # ── Finalize result ────────────────────────────────────────
        result["query"] = question
        result["candidates_retrieved"] = len(candidates)
        result["chunks_after_rerank"] = len(reranked)
        result["cache_hit"] = False

        if not result["declined"]:
            self._cache.set(question, {**result, "cache_hit": True})

        if verbose:
            self._print_result(result)

        return result

    def _print_result(self, result: dict):
        if result["declined"]:
            console.print(Panel(
                f"[yellow]⚠ DECLINED[/yellow]\n\n{result['answer']}",
                title="Answer (Declined)", style="yellow",
            ))
        else:
            console.print(Panel(
                result["answer"],
                title=f"Answer (confidence: {result['confidence']:.2f})",
                style="green",
            ))
            if result.get("sources"):
                table = Table(title="Sources Cited", show_header=True)
                table.add_column("#", style="dim", width=3)
                table.add_column("Title", style="bold")
                table.add_column("URL", style="blue")
                for src in result["sources"]:
                    table.add_row(
                        str(src["index"]),
                        src["title"],
                        src["url"][:60] + "..." if len(src["url"]) > 60 else src["url"],
                    )
                console.print(table)

        # Show corrective RAG stats if available
        crag = result.get("corrective_rag", {})
        if crag:
            kept = crag.get("chunks_kept", "?")
            filtered = crag.get("chunks_filtered", "?")
            retries = crag.get("retries", 0)
            rewritten = crag.get("rewritten_query")
            crag_tag = f"cRAG: {kept} kept, {filtered} filtered"
            if retries > 0:
                crag_tag += f", {retries} rewrite(s)"
            if rewritten:
                crag_tag += f' → "{rewritten[:40]}"'
        else:
            crag_tag = ""

        cache_tag = "⚡ cached" if result.get("cache_hit") else f"prompt_v{result.get('prompt_version', '?')}"
        extras = f" | {crag_tag}" if crag_tag else ""

        console.print(
            f"\n[dim]Stats: {result.get('candidates_retrieved', 0)} retrieved → "
            f"{result.get('chunks_after_rerank', 0)} reranked → "
            f"{result.get('chunks_cited', 0)} cited | {cache_tag}{extras}[/dim]"
        )
