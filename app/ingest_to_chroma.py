"""
Split raw_pages.json into chunks, embed them, store in Chroma.
Run: python -m app.ingest_to_chroma
"""

import os
import json
import time

from dotenv import load_dotenv
from google import genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb

load_dotenv()

# ---------- 1. 读原始页面 ----------
with open("data/raw_pages.json", encoding="utf-8") as f:
    pages = json.load(f)

print(f"Loaded {len(pages)} pages")

# ---------- 2. 切 chunk ----------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""],
)

chunks = []
for page in pages:
    slug = page["url"].split("/")[-1].replace(".html", "")
    for i, piece in enumerate(splitter.split_text(page["text"])):
        chunks.append({
            "id": f"{slug}_{i}",
            "text": piece,
            "url": page["url"],
            "title": page["title"],
        })

print(f"Total chunks: {len(chunks)}")

# ---------- 3. 连 Chroma ----------
chroma = chromadb.PersistentClient(path="./chroma_db")
collection = chroma.get_or_create_collection("postgres_docs")

# 如果之前跑过，先清空，避免重复
if collection.count() > 0:
    print(f"Collection already has {collection.count()} items, deleting...")
    chroma.delete_collection("postgres_docs")
    collection = chroma.get_or_create_collection("postgres_docs")

# ---------- 4. 分批 embed + 写入 ----------
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

BATCH = 10
for start in range(0, len(chunks), BATCH):
    batch = chunks[start:start + BATCH]
    texts = [c["text"] for c in batch]

    resp = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
    )
    embeddings = [e.values for e in resp.embeddings]

    collection.add(
        ids=[c["id"] for c in batch],
        documents=texts,
        embeddings=embeddings,
        metadatas=[{"url": c["url"], "title": c["title"]} for c in batch],
    )
    done = min(start + BATCH, len(chunks))
    print(f"  embedded {done}/{len(chunks)}")
    time.sleep(10)  # 避免触发放免费层速率限制

print(f"\nDone. Collection count: {collection.count()}")