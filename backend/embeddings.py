"""
Embedding Engine: Qwen & Deterministic Semantic Fallback
========================================================
Generates normalized 1536-dimensional vector embeddings for candidate CV sections
and Job Descriptions.

Architecture:
    1. Primary Provider: Qwen3-Embedding-8B (`qwen/qwen3-embedding-8b`) via OpenRouter API.
    2. Zero-Cost / Offline Fallback: Deterministic semantic clustering embedder that computes
       skill-cluster-weighted 1536-dim normalized vectors guaranteeing realistic cosine
       similarity across domains (FastAPI, React, Kubernetes, Distributed Systems, ML/RAG, etc.).
"""

import os
import math
import hashlib
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

# Qwen Embedding Model configured on OpenRouter
QWEN_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen/qwen3-embedding-8b")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


def get_qwen_embedding_cloud(text: str, api_key: str = None) -> list[float] | None:
    """
    Calls OpenRouter embeddings API to generate a vector from the Qwen embedding model.

    Parameters:
        text: Text string to embed (truncated to 2000 chars for token limits).
        api_key: Optional explicit API key; defaults to OPENROUTER_API_KEY env var.

    Returns:
        list[float] | None: Normalized 1536-dim vector if successful; None if failed.
    """
    key = api_key or OPENROUTER_API_KEY
    if not key:
        return None
        
    url = "https://openrouter.ai/api/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost:8000",
        "X-Title": "Recruitment Copilot"
    }
    payload = {
        "model": QWEN_EMBEDDING_MODEL,
        "input": text[:2000] # Safe token length limit per chunk
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            vec = data["data"][0]["embedding"]
            # Ensure dimensionality matches database schema (1536)
            if len(vec) > 1536:
                vec = vec[:1536]
            elif len(vec) < 1536:
                vec = vec + [0.0] * (1536 - len(vec))
            norm = math.sqrt(sum(x * x for x in vec))
            return [x / norm for x in vec] if norm > 0 else vec
    except Exception as e:
        print(f"Warning: Cloud Qwen embedding unavailable ({e}), using deterministic semantic embedder.")
        return None


def get_deterministic_semantic_vector(text: str, dim: int = 1536) -> list[float]:
    """
    Deterministic semantic clustering embedder for offline / test environments.
    Guarantees meaningful cosine similarity across technical domain clusters.

    Clusters covered:
        - Python & FastAPI backend
        - React & modern frontend
        - DevOps, Cloud, & Kubernetes
        - Distributed systems & Kafka
        - AI, LLMs, & RAG
        - Product management & Agile
        - Data engineering & SQL
        - QA & automated testing

    Parameters:
        text: Input string to embed.
        dim: Target vector dimensionality (default: 1536).

    Returns:
        list[float]: L2-normalized vector of length `dim`.
    """
    clusters = {
        "python_fastapi": ["python", "fastapi", "asyncio", "celery", "django", "backend", "rest"],
        "react_frontend": ["react", "frontend", "typescript", "tailwind", "next.js", "ui/ux", "css", "redux"],
        "devops_cloud": ["kubernetes", "docker", "terraform", "aws", "ci/cd", "helm", "devops", "cloud", "eks"],
        "distributed_systems": ["distributed", "kafka", "microservices", "grpc", "throughput", "concurrency", "go"],
        "ai_ml_rag": ["machine learning", "pytorch", "llm", "rag", "vector", "pgvector", "ai", "embeddings", "langchain"],
        "product_mgmt": ["product", "agile", "roadmap", "strategy", "user research", "jira"],
        "data_eng": ["spark", "airflow", "snowflake", "etl", "dbt", "data engineer", "sql"],
        "qa_testing": ["playwright", "cypress", "selenium", "qa", "pytest", "automation", "testing"]
    }
    
    text_lower = text.lower()
    vec = [0.0] * dim
    
    # Base deterministic noise hash from input text
    h = hashlib.sha256(text.encode("utf-8")).digest()
    for i in range(dim):
        byte_val = h[i % len(h)]
        vec[i] = ((byte_val / 255.0) - 0.5) * 0.1
    
    # Assign cluster weights into distinct vector subspaces
    band_size = dim // len(clusters)
    for idx, (cluster_name, keywords) in enumerate(clusters.items()):
        weight = sum(1.0 for kw in keywords if kw in text_lower)
        if weight > 0:
            start_idx = idx * band_size
            for j in range(start_idx, min(start_idx + band_size, dim)):
                vec[j] += weight * 0.8
                
    # Normalize to unit length for cosine similarity
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm > 0 else vec


def get_embedding(text: str, api_key: str = None) -> list[float]:
    """
    Unified embedding pipeline entry point:
    Attempts cloud Qwen embedding via OpenRouter first; falls back to deterministic
    semantic clustering embedder if API key is absent or network fails.

    Parameters:
        text: Text string to embed.
        api_key: Optional explicit OpenRouter API key.

    Returns:
        list[float]: Normalized 1536-dimensional vector embedding.
    """
    vec = get_qwen_embedding_cloud(text, api_key)
    if vec is not None:
        return vec
    return get_deterministic_semantic_vector(text)


if __name__ == "__main__":
    test_text = "Senior Python Backend Engineer with FastAPI and PostgreSQL"
    v = get_embedding(test_text)
    print(f"Embedding generated! Length: {len(v)}, First 5 values: {v[:5]}")
