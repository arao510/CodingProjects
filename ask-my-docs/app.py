"""
app.py
FastAPI backend serving the RAG UI.
Run with: uvicorn app:app --reload
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import json

app = FastAPI(title="Ask My Docs")

# Mount static files
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

# Lazy-load pipeline so server starts fast
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from src.pipeline import RAGPipeline
        _pipeline = RAGPipeline()
    return _pipeline


class QueryRequest(BaseModel):
    question: str


@app.get("/")
async def index():
    return FileResponse("ui/index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/query")
async def query(req: QueryRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question too long (max 500 chars).")

    try:
        pipeline = get_pipeline()
        result = pipeline.query(question, verbose=False)
        return {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "declined": result.get("declined", False),
            "confidence": result.get("confidence", 0),
            "chunks_retrieved": result.get("candidates_retrieved", 0),
            "chunks_reranked": result.get("chunks_after_rerank", 0),
            "chunks_cited": result.get("chunks_cited", 0),
            "cache_hit": result.get("cache_hit", False),
            "prompt_version": result.get("prompt_version", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/suggestions")
async def suggestions():
    """Sample questions to show in the UI."""
    return {"questions": [
        "What is the AWS shared responsibility model?",
        "How does Amazon GuardDuty detect threats?",
        "What are IAM best practices for securing AWS accounts?",
        "What is the OWASP Top 10?",
        "How does SageMaker handle model deployment?",
        "What are VPC security groups?",
        "How does AWS CloudTrail work?",
        "What is AWS HIPAA compliance?",
    ]}
