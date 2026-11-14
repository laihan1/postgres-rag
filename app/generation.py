"""
生成基线：根据检索到的 chunk，让 Gemini 生成有引用的回答。
用法: python -m app.generation "你的问题"
"""

import os
import sys
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.retrieval import retrieve

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=120_000),
)

MODEL = "gemini-3.5-flash-lite"

REFUSAL = "I cannot find a reliable answer in the provided documents."


def build_prompt(question: str, retrieved: dict) -> str:
    """构建包含上下文和问题的完整提示词。"""
    context_parts = []
    for cid, doc in zip(retrieved["ids"], retrieved["documents"]):
        context_parts.append(f"[{cid}]\n{doc}")
    context = "\n\n".join(context_parts)

    return f"""Answer the question using ONLY the context below.

Rules:
- Cite the chunk id in square brackets after each factual statement, e.g. [chunk_123].
- If the answer is not in the context, respond exactly with: "{REFUSAL}"
- Do not use outside knowledge.

Context:
{context}

Question: {question}

Answer:"""


def generate(question: str) -> dict:
    """执行检索并生成回答。"""
    # 1. 检索
    retrieved = retrieve(question, top_k=5)
    # 2. 构建提示词
    prompt = build_prompt(question, retrieved)
    # 3. 调用 Gemini 生成回答 (修正为 input 参数)
    interaction = client.interactions.create(
        model=MODEL,
        input=prompt,
    )

    # 4. 提取回答文本 (正确的方法是 output_text)
    answer = interaction.output_text.strip()

    # 5. 分析回答
    cited = re.findall(r"\[([a-zA-Z0-9_\-]+_\d+)\]", answer)
    grounded = len(cited) > 0
    refused = REFUSAL.lower() in answer.lower()

    return {
        "question": question,
        "answer": answer,
        "sources": retrieved["ids"],
        "cited": cited,
        "grounded": grounded,
        "refused": refused,
        "distances": retrieved["distances"],
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('用法: python -m app.generation "你的问题"')
        sys.exit(1)

    q = sys.argv[1]
    out = generate(q)

    print(f"\nQ: {out['question']}\n")
    print(f"A: {out['answer']}\n")
    print(f"Cited: {out['cited']}")
    print(f"Grounded: {out['grounded']}  Refused: {out['refused']}")
    print(f"Retrieved: {out['sources']}")