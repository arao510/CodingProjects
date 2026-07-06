"""
app_compare.py
FastAPI backend for the RAG comparison UI.
Supports multiple datasets — switch on the fly from the UI.
"""

import os, sys, time, hashlib, json, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import tiktoken

app = FastAPI(title="RAG Comparison Lab")
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

_tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(_tokenizer.encode(text))

# ── Shared singletons — one instance each, reused across all requests ─────────
_vector_store   = None
_bm25_index     = None
_reranker       = None
_std_pipeline   = None
_cor_pipeline   = None
_active_dataset = "aws_cloud"


def get_shared_components():
    """Load heavy models once and reuse them."""
    global _vector_store, _bm25_index, _reranker
    import yaml
    with open("config/prompts.yaml") as f:
        cfg = yaml.safe_load(f)

    if _vector_store is None:
        from src.retrieval.vector_store import VectorStore
        _vector_store = VectorStore(model_name=cfg["models"]["embedding"])

    if _bm25_index is None:
        from src.retrieval.bm25_index import BM25Index
        _bm25_index = BM25Index()
        _bm25_index.load()   # load from cache if available

    if _reranker is None:
        from src.reranking.reranker import CrossEncoderReranker
        _reranker = CrossEncoderReranker(model_name=cfg["models"]["reranker"])

    return _vector_store, _bm25_index, _reranker


def build_pipelines():
    """Build both pipelines sharing the same vector store, BM25, and reranker."""
    global _std_pipeline, _cor_pipeline
    import yaml
    with open("config/prompts.yaml") as f:
        cfg = yaml.safe_load(f)

    vs, bm25, reranker = get_shared_components()

    from src.retrieval.hybrid_retriever import HybridRetriever
    hybrid = HybridRetriever(
        vector_store=vs,
        bm25_index=bm25,
        top_k_initial=cfg["retrieval"]["top_k_initial"],
    )

    from src.generation.generator import AnswerGenerator
    generator = AnswerGenerator()

    from src.corrective.corrective_rag import CorrectiveRAG
    corrective = CorrectiveRAG(hybrid, reranker, generator)

    # Standard pipeline — corrective disabled
    class SimplePipeline:
        def __init__(self):
            self.hybrid_retriever = hybrid
            self.reranker = reranker
            self.generator = generator
            self._cache = {}
            self.config = cfg

        def query(self, question: str, verbose: bool = False) -> dict:
            top_k_i = self.config["retrieval"]["top_k_initial"]
            top_k_f = self.config["retrieval"]["top_k_final"]
            candidates = self.hybrid_retriever.retrieve(question, top_k=top_k_i)
            reranked   = self.reranker.rerank(question, candidates, top_k=top_k_f)
            result     = self.generator.generate(question, reranked)
            result["candidates_retrieved"]  = len(candidates)
            result["chunks_after_rerank"]   = len(reranked)
            result["cache_hit"]             = False
            result["corrective_rag"]        = {}
            return result

    # Corrective pipeline
    class CorrectivePipeline:
        def __init__(self):
            self.hybrid_retriever = hybrid
            self.reranker = reranker
            self.corrective_rag = corrective
            self.config = cfg

        def query(self, question: str, verbose: bool = False) -> dict:
            top_k_i = self.config["retrieval"]["top_k_initial"]
            top_k_f = self.config["retrieval"]["top_k_final"]
            candidates = self.hybrid_retriever.retrieve(question, top_k=top_k_i)
            reranked   = self.reranker.rerank(question, candidates, top_k=top_k_f)
            result     = self.corrective_rag.run(question, reranked)
            result["candidates_retrieved"] = len(candidates)
            result["chunks_after_rerank"]  = len(reranked)
            result["cache_hit"]            = False
            return result

    _std_pipeline = SimplePipeline()
    _cor_pipeline = CorrectivePipeline()


def run_pipeline(pipeline, question: str, system_name: str) -> dict:
    start  = time.time()
    result = pipeline.query(question, verbose=False)
    latency_ms = int((time.time() - start) * 1000)

    answer_tokens  = count_tokens(result.get("answer", ""))
    context_tokens = sum(count_tokens(s.get("excerpt", "")) for s in result.get("sources", []))
    crag = result.get("corrective_rag", {})

    return {
        "system":   system_name,
        "answer":   result.get("answer", ""),
        "sources":  result.get("sources", []),
        "declined": result.get("declined", False),
        "confidence": round(result.get("confidence", 0), 3),
        "metrics": {
            "latency_ms":      latency_ms,
            "total_tokens":    answer_tokens + context_tokens,
            "answer_tokens":   answer_tokens,
            "context_tokens":  context_tokens,
            "chunks_retrieved":result.get("candidates_retrieved", 0),
            "chunks_reranked": result.get("chunks_after_rerank", 0),
            "chunks_cited":    result.get("chunks_cited", 0),
            "chunks_kept":     crag.get("chunks_kept", result.get("chunks_after_rerank", 0)),
            "chunks_filtered": crag.get("chunks_filtered", 0),
            "query_rewrites":  crag.get("retries", 0),
            "rewritten_query": crag.get("rewritten_query"),
            "cache_hit":       result.get("cache_hit", False),
        }
    }


# ── Dataset ingestion ─────────────────────────────────────────────────────────
def ingest_dataset(dataset_id: str) -> dict:
    """
    Fetches, chunks, and indexes a dataset into the SHARED vector store.
    Resets and repopulates the same ChromaDB collection in place —
    no new VectorStore instances created, so pipelines stay valid.
    """
    global _bm25_index, _std_pipeline, _cor_pipeline

    from src.ingestion.datasets import get_dataset
    from src.ingestion.corpus_fetcher import fetch_page
    from src.ingestion.chunker import chunk_document
    from src.retrieval.bm25_index import BM25Index
    import yaml

    dataset = get_dataset(dataset_id)
    if not dataset:
        raise ValueError(f"Dataset '{dataset_id}' not found.")

    with open("config/prompts.yaml") as f:
        config = yaml.safe_load(f)
    chunk_cfg = config["chunking"]

    # Get the shared vector store and reset it in place
    vs, _, _ = get_shared_components()
    vs.reset()   # wipes and recreates the ChromaDB collection in the same object

    # Remove BM25 cache
    bm25_path = Path(".bm25_index.pkl")
    if bm25_path.exists():
        bm25_path.unlink()

    # Fetch documents (with per-dataset cache)
    docs = []
    corpus_dir = Path("corpus") / dataset_id
    corpus_dir.mkdir(parents=True, exist_ok=True)

    for source in dataset["sources"]:
        doc_id     = hashlib.md5(source["url"].encode()).hexdigest()[:8]
        cache_file = corpus_dir / f"{doc_id}.json"

        if cache_file.exists():
            with open(cache_file) as f:
                docs.append(json.load(f))
            continue

        text = fetch_page(source["url"])
        if not text or len(text) < 200:
            continue

        doc = {
            "id": doc_id, "title": source["title"],
            "domain": source["domain"], "url": source["url"],
            "content": text, "char_count": len(text),
        }
        with open(cache_file, "w") as f:
            json.dump(doc, f, indent=2)
        docs.append(doc)
        time.sleep(0.3)

    if not docs:
        raise ValueError("No documents could be fetched for this dataset.")

    # Chunk
    all_chunks = []
    for doc in docs:
        chunks = chunk_document(
            doc,
            target_tokens=chunk_cfg["target_tokens"],
            overlap_tokens=chunk_cfg["overlap_tokens"],
            min_tokens=chunk_cfg["min_chunk_tokens"],
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("No chunks produced — documents may be too short.")

    # Embed into the shared vector store (already reset above)
    vs.add_chunks(all_chunks)

    # Build new BM25 index and store in the shared singleton
    chunk_dicts = [
        {"chunk_id": c.chunk_id, "content": c.content, "doc_id": c.doc_id,
         "doc_title": c.doc_title, "doc_url": c.doc_url, "domain": c.domain,
         "chunk_index": c.chunk_index, "total_chunks": c.total_chunks,
         "token_count": c.token_count}
        for c in all_chunks
    ]
    new_bm25 = BM25Index()
    new_bm25.build(chunk_dicts)

    # Update the shared BM25 singleton in place so existing pipeline refs see it
    global _bm25_index
    if _bm25_index is not None:
        _bm25_index.bm25   = new_bm25.bm25
        _bm25_index.chunks = new_bm25.chunks
    else:
        _bm25_index = new_bm25

    # Rebuild pipelines so HybridRetriever picks up the updated BM25
    build_pipelines()

    return {
        "dataset_id":    dataset_id,
        "dataset_name":  dataset["name"],
        "docs_fetched":  len(docs),
        "chunks_indexed":len(all_chunks),
        "embeddings":    vs.count(),
    }


# ── Startup — load default dataset ───────────────────────────────────────────
@app.on_event("startup")
async def startup():
    """Initialize pipelines on server start."""
    try:
        get_shared_components()   # load models
        build_pipelines()         # wire everything together
    except Exception as e:
        print(f"Startup warning: {e}")


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse("ui/compare.html")

@app.get("/health")
async def health():
    vs = _vector_store
    return {
        "status": "ok",
        "active_dataset": _active_dataset,
        "chunks_indexed": vs.count() if vs else 0,
    }


@app.get("/api/datasets")
async def list_datasets():
    from src.ingestion.datasets import get_all_datasets
    datasets = get_all_datasets()
    return {
        "active": _active_dataset,
        "datasets": [
            {
                "id": k,
                "name": v["name"],
                "description": v["description"],
                "icon": v.get("icon", "📄"),
                "color": v.get("color", "#64748B"),
                "source_count": len(v["sources"]),
                "is_custom": v.get("is_custom", False),
            }
            for k, v in datasets.items()
        ]
    }


class SwitchDatasetRequest(BaseModel):
    dataset_id: str


@app.post("/api/switch-dataset")
async def switch_dataset(req: SwitchDatasetRequest):
    global _active_dataset
    from src.ingestion.datasets import get_dataset

    dataset = get_dataset(req.dataset_id)
    if not dataset:
        raise HTTPException(404, f"Dataset '{req.dataset_id}' not found.")

    try:
        result = ingest_dataset(req.dataset_id)
        _active_dataset = req.dataset_id
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(500, str(e))


class CustomDatasetRequest(BaseModel):
    name: str
    description: str
    urls: list[str]


@app.post("/api/add-custom-dataset")
async def add_custom_dataset(req: CustomDatasetRequest):
    from src.ingestion.datasets import save_custom_dataset

    if not req.urls:
        raise HTTPException(400, "Must provide at least one URL.")
    if len(req.urls) > 30:
        raise HTTPException(400, "Maximum 30 URLs per custom dataset.")

    sources = []
    for url in req.urls:
        url = url.strip()
        if not url.startswith("http"):
            continue
        clean = re.sub(r'https?://(www\.)?', '', url).rstrip('/')
        title = clean.split('/')[-1].replace('-', ' ').replace('_', ' ').title() or clean[:40]
        sources.append({"url": url, "domain": "custom", "title": title[:60]})

    if not sources:
        raise HTTPException(400, "No valid URLs provided.")

    dataset_id = "custom_" + hashlib.md5(req.name.encode()).hexdigest()[:6]
    dataset = {
        "name": req.name[:50],
        "description": req.description[:120],
        "icon": "📄",
        "color": "#64748B",
        "sources": sources,
        "is_custom": True,
    }
    save_custom_dataset(dataset_id, dataset)
    return {"success": True, "dataset_id": dataset_id, "source_count": len(sources)}


class QueryRequest(BaseModel):
    question: str


@app.post("/api/compare")
async def compare(req: QueryRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(400, "Question cannot be empty.")
    if len(question) > 500:
        raise HTTPException(400, "Question too long (max 500 chars).")

    if _std_pipeline is None or _cor_pipeline is None:
        raise HTTPException(503, "Pipelines not ready — run ingest.py first or switch a dataset.")

    vs = _vector_store
    if vs and vs.count() == 0:
        raise HTTPException(503, "No documents indexed. Please select a dataset first.")

    with ThreadPoolExecutor(max_workers=2) as executor:
        std_future = executor.submit(run_pipeline, _std_pipeline, question, "standard")
        cor_future = executor.submit(run_pipeline, _cor_pipeline, question, "corrective")
        try:
            std_result = std_future.result(timeout=120)
        except Exception as e:
            raise HTTPException(500, f"Standard RAG error: {e}")
        try:
            cor_result = cor_future.result(timeout=120)
        except Exception as e:
            raise HTTPException(500, f"Corrective RAG error: {e}")

    return {
        "question":   question,
        "dataset":    _active_dataset,
        "standard":   std_result,
        "corrective": cor_result,
    }


@app.get("/api/suggestions")
async def suggestions():
    suggestion_map = {
        "aws_cloud": ["What is the AWS shared responsibility model?","What are the five pillars of the AWS Well-Architected Framework?","How does Amazon GuardDuty detect threats?","What are IAM best practices?","How does AWS CloudTrail work?","What are VPC security groups?"],
        "cybersecurity": ["What are the OWASP Top 10 vulnerabilities?","What is SQL injection?","What is the NIST Cybersecurity Framework?","What is sensitive data exposure?","How does GDPR affect compliance?","What is zero trust security?"],
        "machine_learning": ["What is Amazon SageMaker?","How does SageMaker handle model training?","What is deep learning?","What is natural language processing?","How does Amazon Bedrock work?","What is a neural network?"],
        "web_development": ["What is an HTTP status code?","How do HTTP cookies work?","What is a REST API?","How does CSS Grid work?","What is the Fetch API?","What is NoSQL?"],
        "devops": ["What is DevOps?","What is continuous integration?","What is Kubernetes?","What is infrastructure as code?","How does auto scaling work?","What are microservices?"],
    }
    questions = suggestion_map.get(_active_dataset, ["What is the main topic of this dataset?","Summarize the key concepts in this documentation."])
    return {"questions": questions}