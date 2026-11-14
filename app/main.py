"""
FastAPI 服务化
启动: uvicorn app.main:app --reload
测试: http://127.0.0.1:8000/docs
"""

import time

from fastapi import FastAPI
from pydantic import BaseModel

from app.generation import generate

app = FastAPI(title="PostgreSQL RAG API")


class Question(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str
    sources: list[str]
    cited: list[str]
    grounded: bool
    refused: bool
    latency_ms: int


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}


@app.post("/ask", response_model=Answer)
def ask(q: Question):
    start = time.time()
    result = generate(q.question)
    latency = int((time.time() - start) * 1000)

    return Answer(
        answer=result["answer"],
        sources=result["sources"],
        cited=result["cited"],
        grounded=result["grounded"],
        refused=result["refused"],
        latency_ms=latency,
    )