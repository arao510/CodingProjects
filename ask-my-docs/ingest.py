"""
ingest.py
One-shot ingestion script: fetch → chunk → embed → BM25 index.
Run this first before querying.

Usage:
    python ingest.py              # full ingest
    python ingest.py --reset      # wipe and re-ingest
    python ingest.py --stats      # show index stats
"""

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent))

console = Console()


def main(reset: bool = False, stats_only: bool = False):
    console.print(Panel(
        "[bold cyan]RAG System — Document Ingestion[/bold cyan]\n"
        "Phase 1 & 2: Fetch → Chunk → Embed → BM25 Index",
        style="cyan"
    ))

    # ── Load config ────────────────────────────────────────────────
    import yaml
    with open("config/prompts.yaml") as f:
        config = yaml.safe_load(f)
    chunk_cfg = config["chunking"]
    model_cfg = config["models"]

    # ── Vector store ───────────────────────────────────────────────
    from src.retrieval.vector_store import VectorStore
    vs = VectorStore(model_name=model_cfg["embedding"])

    if stats_only:
        console.print(f"\n[bold]Vector store:[/bold] {vs.count()} chunks indexed")
        from src.retrieval.bm25_index import BM25Index
        bm25 = BM25Index()
        if bm25.load():
            console.print(f"[bold]BM25 index:[/bold] {len(bm25.chunks)} chunks")
        return

    if reset:
        vs.reset()
        import os
        if os.path.exists(".bm25_index.pkl"):
            os.remove(".bm25_index.pkl")
        console.print("[yellow]Indexes reset.[/yellow]")

    # ── Fetch corpus ───────────────────────────────────────────────
    console.print("\n[bold]Step 1/4: Fetching corpus documents...[/bold]")
    from src.ingestion.corpus_fetcher import build_corpus
    docs = build_corpus("corpus")

    if not docs:
        console.print("[red]❌ No documents fetched. Check network connectivity.[/red]")
        sys.exit(1)

    # ── Chunk documents ────────────────────────────────────────────
    console.print("\n[bold]Step 2/4: Chunking documents...[/bold]")
    from src.ingestion.chunker import chunk_corpus
    chunks = chunk_corpus(
        docs,
        target_tokens=chunk_cfg["target_tokens"],
        overlap_tokens=chunk_cfg["overlap_tokens"],
        min_tokens=chunk_cfg["min_chunk_tokens"],
    )

    if not chunks:
        console.print("[red]❌ No chunks produced.[/red]")
        sys.exit(1)

    # ── Embed and store in ChromaDB ────────────────────────────────
    console.print("\n[bold]Step 3/4: Embedding chunks into vector store...[/bold]")

    # Convert Chunk dataclasses to dicts for the vector store
    chunk_dicts = [
        {
            "chunk_id": c.chunk_id,
            "content": c.content,
            "doc_id": c.doc_id,
            "doc_title": c.doc_title,
            "doc_url": c.doc_url,
            "domain": c.domain,
            "chunk_index": c.chunk_index,
            "total_chunks": c.total_chunks,
            "token_count": c.token_count,
        }
        for c in chunks
    ]

    vs.add_chunks(chunks)

    # ── Build BM25 index ───────────────────────────────────────────
    console.print("\n[bold]Step 4/4: Building BM25 keyword index...[/bold]")
    from src.retrieval.bm25_index import BM25Index
    bm25 = BM25Index()
    bm25.build(chunk_dicts)

    console.print(Panel(
        f"[bold green]✅ Ingestion complete![/bold green]\n\n"
        f"Documents: {len(docs)}\n"
        f"Chunks: {len(chunks)}\n"
        f"Vector store: {vs.count()} embeddings\n"
        f"BM25 index: {len(bm25.chunks)} entries",
        style="green"
    ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest corpus into RAG indexes")
    parser.add_argument("--reset", action="store_true", help="Wipe and re-ingest")
    parser.add_argument("--stats", action="store_true", help="Show index stats and exit")
    args = parser.parse_args()

    main(reset=args.reset, stats_only=args.stats)
