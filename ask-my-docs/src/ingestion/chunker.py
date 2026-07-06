"""
chunker.py
Token-aware document chunker: 500-800 tokens per chunk, ~100 token overlap.
Uses tiktoken for accurate token counting.
"""

import re
import uuid
import tiktoken
from dataclasses import dataclass, field
from rich.console import Console

console = Console()

# Use cl100k_base (GPT-4 / Claude compatible tokenizer approximation)
TOKENIZER = tiktoken.get_encoding("cl100k_base")


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    doc_title: str
    doc_url: str
    domain: str
    content: str
    token_count: int
    chunk_index: int       # position within parent doc
    total_chunks: int      # total chunks from parent doc (filled in later)
    metadata: dict = field(default_factory=dict)


def count_tokens(text: str) -> int:
    return len(TOKENIZER.encode(text))


def split_into_sentences(text: str) -> list[str]:
    """
    Splits text into sentence-level units.
    Prefers splitting on sentence boundaries to keep chunks coherent.
    """
    # Split on sentence-ending punctuation followed by whitespace
    pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    parts = re.split(pattern, text)

    # Also split on double newlines (paragraph breaks)
    result = []
    for part in parts:
        sub = re.split(r'\n\n+', part.strip())
        result.extend(s.strip() for s in sub if s.strip())

    return result


def chunk_document(
    doc: dict,
    target_tokens: int = 650,
    overlap_tokens: int = 100,
    min_tokens: int = 100,
) -> list[Chunk]:
    """
    Chunks a single document into overlapping token windows.

    Strategy:
    1. Split document into sentence-level units
    2. Greedily pack sentences into chunks up to target_tokens
    3. When a chunk fills up, carry the last `overlap_tokens` worth of
       sentences into the next chunk for context continuity
    """
    content = doc["content"]
    sentences = split_into_sentences(content)

    if not sentences:
        return []

    chunks: list[Chunk] = []
    current_sentences: list[str] = []
    current_tokens: int = 0

    def flush_chunk(sentences: list[str], index: int) -> Chunk | None:
        text = " ".join(sentences).strip()
        tok = count_tokens(text)
        if tok < min_tokens:
            return None
        return Chunk(
            chunk_id=str(uuid.uuid4()),
            doc_id=doc["id"],
            doc_title=doc["title"],
            doc_url=doc["url"],
            domain=doc["domain"],
            content=text,
            token_count=tok,
            chunk_index=index,
            total_chunks=0,  # filled after all chunks known
        )

    for sentence in sentences:
        sent_tokens = count_tokens(sentence)

        # If a single sentence is huge, truncate it
        if sent_tokens > target_tokens:
            words = sentence.split()
            sentence = " ".join(words[:target_tokens])
            sent_tokens = count_tokens(sentence)

        if current_tokens + sent_tokens > target_tokens and current_sentences:
            chunk = flush_chunk(current_sentences, len(chunks))
            if chunk:
                chunks.append(chunk)

            # Build overlap: walk back from end until we have ~overlap_tokens
            overlap_sents = []
            overlap_count = 0
            for s in reversed(current_sentences):
                st = count_tokens(s)
                if overlap_count + st > overlap_tokens:
                    break
                overlap_sents.insert(0, s)
                overlap_count += st

            current_sentences = overlap_sents + [sentence]
            current_tokens = overlap_count + sent_tokens
        else:
            current_sentences.append(sentence)
            current_tokens += sent_tokens

    # Flush last chunk
    if current_sentences:
        chunk = flush_chunk(current_sentences, len(chunks))
        if chunk:
            chunks.append(chunk)

    # Fill in total_chunks
    for c in chunks:
        c.total_chunks = len(chunks)

    return chunks


def chunk_corpus(docs: list[dict], **kwargs) -> list[Chunk]:
    """Chunks all documents in the corpus."""
    all_chunks: list[Chunk] = []

    for doc in docs:
        doc_chunks = chunk_document(doc, **kwargs)
        all_chunks.extend(doc_chunks)
        console.print(
            f"  [dim]{doc['title']}[/dim] → [cyan]{len(doc_chunks)} chunks[/cyan] "
            f"([dim]{doc_chunks[0].token_count if doc_chunks else 0}–"
            f"{doc_chunks[-1].token_count if doc_chunks else 0} tokens[/dim])"
        )

    token_counts = [c.token_count for c in all_chunks]
    if token_counts:
        console.print(
            f"\n[green]✅ {len(all_chunks)} total chunks | "
            f"avg {sum(token_counts)//len(token_counts)} tokens | "
            f"min {min(token_counts)} | max {max(token_counts)}[/green]"
        )

    return all_chunks


if __name__ == "__main__":
    # Quick smoke test
    test_doc = {
        "id": "test001",
        "title": "Test Document",
        "url": "http://example.com",
        "domain": "test",
        "content": " ".join([
            f"This is sentence number {i} about machine learning and RAG systems."
            for i in range(200)
        ])
    }
    chunks = chunk_document(test_doc)
    print(f"Produced {len(chunks)} chunks")
    for c in chunks[:3]:
        print(f"  Chunk {c.chunk_index}: {c.token_count} tokens")
