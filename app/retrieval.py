"""
检索基线
用法: python -m app.retrieval "你的问题"
"""

import os
import sys

from dotenv import load_dotenv
from google import genai
import chromadb

load_dotenv()

chroma = chromadb.PersistentClient(path="./chroma_db")
collection = chroma.get_collection("postgres_docs")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def retrieve(question: str, top_k: int = 5):
    """把问题转成向量，从 Chroma 取 top-k 最相似的 chunk。"""
    resp = client.models.embed_content(
        model="gemini-embedding-001",
        contents=[question],
    )
    q_vec = resp.embeddings[0].values

    results = collection.query(
        query_embeddings=[q_vec],
        n_results=top_k,
    )

    return {
        "ids": results["ids"][0],
        "documents": results["documents"][0],
        "metadatas": results["metadatas"][0],
        "distances": results["distances"][0],
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('用法: python -m app.retrieval "你的问题"')
        sys.exit(1)

    q = sys.argv[1]
    out = retrieve(q)
    for i, (cid, doc, meta, dist) in enumerate(
        zip(out["ids"], out["documents"], out["metadatas"], out["distances"]), 1
    ):
        print(f"\n--- [{i}] {cid}  (distance={dist:.4f}) ---")
        print(f"URL: {meta['url']}")
        print(f"Title: {meta['title']}")
        print(doc[:300])