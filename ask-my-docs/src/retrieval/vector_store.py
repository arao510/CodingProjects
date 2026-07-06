"""
vector_store.py
ChromaDB vector store: embed chunks and store for retrieval.
Uses sentence-transformers for local embeddings (no API cost).
"""

import json
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rich.console import Console
from rich.progress import track

from src.ingestion.chunker import Chunk

console = Console()

COLLECTION_NAME = "rag_docs"
PERSIST_DIR = ".chroma_db"


class VectorStore:
    """
    Manages ChromaDB collection for the RAG system.
    Handles embedding, upsert, and semantic search.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        persist_dir: str = PERSIST_DIR,
    ):
        self.model_name = model_name
        self.persist_dir = persist_dir

        console.print(f"[dim]Loading embedding model: {model_name}...[/dim]")
        self.embedder = SentenceTransformer(model_name)

        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # cosine similarity
        )
        console.print(
            f"[green]✅ VectorStore ready — {self.collection.count()} docs in collection[/green]"
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""
        return self.embedder.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,  # cosine similarity works best with L2-normalized
        ).tolist()

    def add_chunks(self, chunks: list[Chunk], batch_size: int = 100) -> int:
        """
        Upsert chunks into ChromaDB.
        Returns number of chunks added.
        """
        if not chunks:
            return 0

        # Check which chunk_ids already exist to avoid re-embedding
        existing_ids = set(self.collection.get(ids=[c.chunk_id for c in chunks])["ids"])
        new_chunks = [c for c in chunks if c.chunk_id not in existing_ids]

        if not new_chunks:
            console.print("[dim]All chunks already indexed — skipping.[/dim]")
            return 0

        console.print(f"[cyan]Embedding {len(new_chunks)} chunks...[/cyan]")

        added = 0
        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i : i + batch_size]
            texts = [c.content for c in batch]
            embeddings = self.embed(texts)

            self.collection.upsert(
                ids=[c.chunk_id for c in batch],
                embeddings=embeddings,
                documents=texts,
                metadatas=[
                    {
                        "doc_id": c.doc_id,
                        "doc_title": c.doc_title,
                        "doc_url": c.doc_url,
                        "domain": c.domain,
                        "chunk_index": c.chunk_index,
                        "total_chunks": c.total_chunks,
                        "token_count": c.token_count,
                    }
                    for c in batch
                ],
            )
            added += len(batch)

        console.print(f"[green]✅ Indexed {added} new chunks[/green]")
        return added

    def search(
        self,
        query: str,
        top_k: int = 20,
        domain_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Semantic search: embed query, return top_k closest chunks.
        Returns list of dicts with content, metadata, and score.
        """
        query_embedding = self.embed([query])[0]

        where_filter = {"domain": domain_filter} if domain_filter else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # ChromaDB returns cosine distance (0=identical, 2=opposite)
            # Convert to similarity score 0-1
            score = 1.0 - (dist / 2.0)
            hits.append(
                {
                    "content": doc,
                    "score": score,
                    "doc_title": meta["doc_title"],
                    "doc_url": meta["doc_url"],
                    "domain": meta["domain"],
                    "chunk_index": meta["chunk_index"],
                    "chunk_id": results["ids"][0][len(hits)],
                }
            )

        return hits

    def count(self) -> int:
        return self.collection.count()

    def reset(self):
        """Delete and recreate the collection (for re-indexing)."""
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        console.print("[yellow]⚠ Collection reset[/yellow]")


if __name__ == "__main__":
    vs = VectorStore()
    print(f"Collection has {vs.count()} chunks")
