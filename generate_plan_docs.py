"""
Generate two Word documents:
  - RAG_Project_Plan_EN.docx
  - RAG_Project_Plan_ZH.docx
Run: python generate_plan_docs.py
"""

from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ---------- helpers ----------

def setup_cjk_font(doc, font_name="Microsoft YaHei"):
    for s in doc.styles:
        try:
            if s.element.rPr is None:
                s.element.get_or_add_rPr()
            rFonts = s.element.rPr.find(qn("w:rFonts"))
            if rFonts is None:
                rFonts = OxmlElement("w:rFonts")
                s.element.rPr.append(rFonts)
            rFonts.set(qn("w:eastAsia"), font_name)
        except Exception:
            pass


def shade_paragraph(p, fill="F2F2F2"):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)


def code_block(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    shade_paragraph(p)


def kv(doc, key, value):
    p = doc.add_paragraph()
    r = p.add_run(key + " ")
    r.bold = True
    p.add_run(value)


def bullets(doc, items):
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def simple_table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = str(v)


# ---------- English document ----------

def build_en():
    doc = Document()
    setup_cjk_font(doc)

    doc.add_heading("RAG Project Plan — AI-Executable Specification", level=0)
    kv(doc, "Project:", "PostgreSQL Documentation RAG System")
    kv(doc, "Goal:", "Build, evaluate, and deploy a citation-grounded document QA service over PostgreSQL official docs.")
    kv(doc, "Stack (fixed):", "Gemini 3.8 Flash (generation), gemini-embedding-001 (embedding), Chroma (vector DB), FastAPI, Docker, Hugging Face Spaces.")
    kv(doc, "Hard rule:", "Do not change the LLM or embedding model between Phase 1 and Phase 5. All evaluation numbers must be comparable.")

    doc.add_heading("Phase -1: Pre-Decisions (Completed)", level=1)
    doc.add_paragraph("Objective: Lock technical choices before writing code.")
    doc.add_paragraph("Decisions:")
    simple_table(doc, ["Item", "Choice"], [
        ["Deployment", "Hybrid (local dev, cloud deploy)"],
        ["LLM", "gemini-3.8-flash via Google AI Studio free tier"],
        ["Embedding", "gemini-embedding-001"],
        ["Vector DB", "Chroma"],
        ["Data", "PostgreSQL 16 official docs (2,000-3,000 chunks)"],
        ["Backend", "FastAPI on Hugging Face Spaces (Docker)"],
        ["Frontend", "FastAPI /docs first; Open WebUI optional"],
        ["API key mgmt", ".env + python-dotenv"],
    ])
    kv(doc, "AI instruction:", "Treat these as constants. Do not substitute models unless the user explicitly requests it.")

    doc.add_heading("Phase 0: Environment and Skeleton (Completed)", level=1)
    doc.add_paragraph("Objective: Create a reproducible project skeleton and push to GitHub.")
    doc.add_paragraph("Tasks:")
    bullets(doc, [
        "Create postgres-rag/ folder",
        "Create app/ with __init__.py, main.py, ingestion.py, retrieval.py, generation.py",
        "Create .env with GEMINI_API_KEY=...",
        "Create .gitignore excluding .env, .venv/, chroma_db/, __pycache__/",
        "git init, commit 'Phase 0: project skeleton', push to https://github.com/laihan1/postgres-rag",
    ])
    kv(doc, "Deliverables:", "Working Python venv, GitHub repo with no .env tracked.")
    kv(doc, "Checkpoint:", "git ls-files does not list .env.")
    kv(doc, "Git status:", "Completed.")

    doc.add_heading("Phase 1: Data Ingestion (1-2 days)", level=1)
    doc.add_paragraph("Objective: Convert PostgreSQL docs into embedded chunks stored in Chroma.")
    doc.add_paragraph("Tasks:")
    bullets(doc, [
        "Download PostgreSQL 16 official docs (PDF or HTML).",
        "Extract plain text.",
        "Split with RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100).",
        "Attach metadata to each chunk: id, text, source, chapter.",
        "Generate embeddings using gemini-embedding-001.",
        "Store in Chroma at ./chroma_db with collection name postgres_docs.",
    ])
    kv(doc, "Deliverables:", "app/ingestion.py runnable; collection.count() returns 2,000-3,000.")
    kv(doc, "Checkpoint:", "A sample query retrieves at least one relevant chunk.")
    kv(doc, "Git commit:", "Phase 1: ingestion pipeline produces <N> chunks")
    kv(doc, "AI instruction:", "Use google-genai SDK. Batch embedding requests. Do not embed empty chunks.")

    doc.add_heading("Phase 2: Retrieval Baseline (1 day)", level=1)
    doc.add_paragraph("Objective: Implement dense-only retrieval and observe failures.")
    bullets(doc, [
        "Write app/retrieval.py with retrieve(question, top_k=5).",
        "Convert question with gemini-embedding-001.",
        "Query Chroma for top 5 chunks.",
        "Return ids, documents, metadatas.",
    ])
    kv(doc, "Deliverables:", "retrieval.py runnable.")
    kv(doc, "Checkpoint:", "Exact-token queries (e.g., max_connections) likely fail. Record these failures.")
    kv(doc, "Git commit:", "Phase 2: baseline dense retrieval")
    kv(doc, "AI instruction:", "Do not add BM25 or reranker yet. Preserve baseline purity.")

    doc.add_heading("Phase 3: Generation Baseline (1 day)", level=1)
    doc.add_paragraph("Objective: Generate citation-grounded answers with refusal behavior.")
    bullets(doc, [
        "Write app/generation.py with generate(question, chunk_ids, chunk_texts).",
        "Build prompt requiring: use only provided context, cite chunk id in [chunk_xxx], refuse if answer absent.",
        "Call gemini-3.8-flash.",
        "Return answer and cited chunk ids.",
    ])
    kv(doc, "Deliverables:", "generation.py runnable.")
    kv(doc, "Checkpoint:", "Answer includes [chunk_xxx]; unanswerable question triggers refusal.")
    kv(doc, "Git commit:", "Phase 3: generation with citation and refusal")
    kv(doc, "AI instruction:", "Validate that the model output contains at least one chunk id. If not, mark grounded=False.")

    doc.add_heading("Phase 4: FastAPI Service (1 day)", level=1)
    doc.add_paragraph("Objective: Expose the RAG pipeline as an HTTP service.")
    bullets(doc, [
        "Write app/main.py with POST /ask.",
        "Request body: {\"question\": \"...\"}",
        "Response: {\"answer\": \"...\", \"sources\": [...], \"grounded\": bool, \"latency_ms\": int}",
        "Run with uvicorn app.main:app --reload.",
        "Test via http://127.0.0.1:8000/docs.",
    ])
    kv(doc, "Deliverables:", "Working /ask endpoint.")
    kv(doc, "Checkpoint:", "Swagger UI returns valid JSON.")
    kv(doc, "Git commit:", "Phase 4: FastAPI endpoint")
    kv(doc, "AI instruction:", "Use Pydantic model for request validation. Include latency measurement.")

    doc.add_heading("Phase 5: Evaluation (2-3 days) — Critical", level=1)
    doc.add_paragraph("Objective: Quantify system quality and document failures.")
    doc.add_paragraph("Tasks:")
    bullets(doc, [
        "Create eval/test_set.json with 30 questions: 10 normal, 10 exact-token, 10 unanswerable.",
        "Write eval/evaluate.py to compute Recall@5, grounding rate, correct refusal rate, p95 latency.",
        "Identify 2-3 concrete failure cases.",
        "Write eval/EVAL.md with baseline metrics and failure analysis.",
    ])
    kv(doc, "Deliverables:", "test_set.json, evaluate.py, EVAL.md.")
    kv(doc, "Checkpoint:", "You can state 'Recall@5 on exact-token questions is X because Y'.")
    kv(doc, "Git commit:", "Phase 5: evaluation - baseline Recall@5 = <X>")
    kv(doc, "AI instruction:", "Do not modify retrieval or generation during evaluation. Report metrics per category, not only overall.")

    doc.add_heading("Phase 6: Dockerization (0.5 day)", level=1)
    doc.add_paragraph("Objective: Make the service reproducible.")
    bullets(doc, [
        "Write Dockerfile for the FastAPI app.",
        "Build and run locally.",
        "Document commands in README.",
    ])
    kv(doc, "Deliverables:", "Working Docker image.")
    kv(doc, "Checkpoint:", "Service runs after docker run -p 8000:8000 <image>.")
    kv(doc, "Git commit:", "Phase 6: Dockerfile")
    kv(doc, "AI instruction:", "Use python:3.11-slim. Expose port 8000. Do not copy .env into image; pass env vars at runtime.")

    doc.add_heading("Phase 7: Deployment (1-2 days)", level=1)
    doc.add_paragraph("Objective: Deploy backend to a public URL.")
    bullets(doc, [
        "Push Docker image to Hugging Face Spaces (Docker SDK).",
        "Verify public /docs endpoint.",
        "Optional: deploy Open WebUI to another Space or Railway and connect to backend.",
        "Confirm service works with your computer turned off.",
    ])
    kv(doc, "Deliverables:", "Public FastAPI URL.")
    kv(doc, "Checkpoint:", "Mobile browser (not on home Wi-Fi) can call /ask.")
    kv(doc, "Git commit:", "Phase 7: deployed to Hugging Face Spaces")
    kv(doc, "AI instruction:", "Set GEMINI_API_KEY as a Space secret. Do not commit the key.")

    doc.add_heading("Phase 8: Iteration — Hybrid Search (Optional, 2-3 days)", level=1)
    doc.add_paragraph("Objective: Improve retrieval using BM25 + dense fusion.")
    bullets(doc, [
        "Add BM25 index over chunk texts.",
        "Merge dense top-20 and BM25 top-20 using Reciprocal Rank Fusion.",
        "Re-run Phase 5 evaluation.",
        "Update EVAL.md with before/after metrics.",
    ])
    kv(doc, "Deliverables:", "Updated retrieval.py, updated EVAL.md.")
    kv(doc, "Checkpoint:", "Recall@5 improves; failures are explained.")
    kv(doc, "Git commit:", "Phase 8: hybrid search - Recall@5 improved from <X> to <Y>")
    kv(doc, "AI instruction:", "Keep generation model unchanged. Compare against Phase 5 baseline only.")

    doc.add_heading("Phase 9: README and Resume Packaging (1 day)", level=1)
    doc.add_paragraph("Objective: Make the repo understandable and resume-ready.")
    bullets(doc, [
        "Write README with: one-sentence description, architecture diagram, how to run (docker build / docker run / curl), evaluation summary, known limitations (2-3 items).",
        "Write 4-line resume bullet using metrics.",
        "Clean repo (no notebooks, no secrets).",
    ])
    kv(doc, "Deliverables:", "Polished GitHub repo and resume bullet.")
    kv(doc, "Checkpoint:", "A friend can run the project using only the README.")
    kv(doc, "Git commit:", "Phase 9: README and project polish")
    kv(doc, "AI instruction:", "Ensure README includes the live demo URL from Phase 7.")

    doc.add_heading("Dependency Graph", level=1)
    code_block(doc,
        "Phase -1 [done] -> Phase 0 [done] -> Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 -> Phase 6 -> Phase 7\n"
        "                                        \\           /\n"
        "                                         Phase 5 <-\n"
        "                                            |\n"
        "                                         Phase 8 (optional)\n"
        "                                            |\n"
        "                                         Phase 9"
    )
    kv(doc, "Rule:", "Phase 5 must finish before Phase 7. Evaluation numbers are required for README and resume.")

    doc.add_heading("Standard Git Routine After Each Phase", level=1)
    code_block(doc, "git add .\ngit commit -m \"Phase N: <description>\"\ngit push")

    doc.save("RAG_Project_Plan_EN.docx")
    print("Saved: RAG_Project_Plan_EN.docx")


# ---------- Chinese document ----------

def build_zh():
    doc = Document()
    setup_cjk_font(doc)

    doc.add_heading("RAG 專案計劃 — AI 可執行規格書", level=0)
    kv(doc, "專案名稱：", "PostgreSQL 文件 RAG 系統")
    kv(doc, "目標：", "建立一個基於 PostgreSQL 官方文件、附引用來源、可評估、可部署的文件問答服務。")
    kv(doc, "固定技術棧：", "Gemini 3.8 Flash（生成）、gemini-embedding-001（嵌入）、Chroma（向量資料庫）、FastAPI、Docker、Hugging Face Spaces。")
    kv(doc, "鐵律：", "Phase 1 到 Phase 5 之間不得更換 LLM 或嵌入模型，所有評估數字必須可比較。")

    doc.add_heading("Phase -1：前置決策（已完成）", level=1)
    doc.add_paragraph("目標：在寫程式前鎖定技術選型。")
    simple_table(doc, ["項目", "選擇"], [
        ["部署方式", "混合（本地開發，雲端部署）"],
        ["LLM", "gemini-3.8-flash（Google AI Studio 免費層）"],
        ["嵌入模型", "gemini-embedding-001"],
        ["向量資料庫", "Chroma"],
        ["資料來源", "PostgreSQL 16 官方文件（2,000–3,000 chunk）"],
        ["後端", "FastAPI，部署到 Hugging Face Spaces（Docker）"],
        ["前端", "先用 FastAPI /docs；Open WebUI 可選"],
        ["API Key 管理", ".env + python-dotenv"],
    ])
    kv(doc, "AI 執行指令：", "以上視為常數。除非使用者明確要求，否則不得替換模型。")

    doc.add_heading("Phase 0：環境與專案骨架（已完成）", level=1)
    doc.add_paragraph("目標：建立可重現的專案骨架並推上 GitHub。")
    bullets(doc, [
        "建立 postgres-rag/ 資料夾",
        "建立 app/，內含 __init__.py、main.py、ingestion.py、retrieval.py、generation.py",
        "建立 .env，寫入 GEMINI_API_KEY=...",
        "建立 .gitignore，排除 .env、.venv/、chroma_db/、__pycache__/",
        "git init，commit 'Phase 0: project skeleton'，push 到 https://github.com/laihan1/postgres-rag",
    ])
    kv(doc, "交付物：", "可用的 Python venv、GitHub repo，且 .env 未被追蹤。")
    kv(doc, "檢查點：", "git ls-files 輸出中沒有 .env。")
    kv(doc, "Git 狀態：", "已完成。")

    doc.add_heading("Phase 1：資料攝入（1–2 天）", level=1)
    doc.add_paragraph("目標：將 PostgreSQL 文件轉成嵌入向量並存入 Chroma。")
    bullets(doc, [
        "下載 PostgreSQL 16 官方文件（PDF 或 HTML）。",
        "抽取純文字。",
        "用 RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100) 切分。",
        "每個 chunk 附加 metadata：id、text、source、chapter。",
        "用 gemini-embedding-001 產生嵌入向量。",
        "存入 Chroma，路徑 ./chroma_db，collection 名稱 postgres_docs。",
    ])
    kv(doc, "交付物：", "app/ingestion.py 可執行；collection.count() 回傳 2,000–3,000。")
    kv(doc, "檢查點：", "隨便一個查詢能檢索到至少一個相關 chunk。")
    kv(doc, "Git commit：", "Phase 1: ingestion pipeline produces <N> chunks")
    kv(doc, "AI 執行指令：", "使用 google-genai SDK。盡量批次送出嵌入請求。不要嵌入空 chunk。")

    doc.add_heading("Phase 2：檢索 Baseline（1 天）", level=1)
    doc.add_paragraph("目標：實作純向量檢索，並觀察失敗案例。")
    bullets(doc, [
        "撰寫 app/retrieval.py，提供 retrieve(question, top_k=5)。",
        "用 gemini-embedding-001 將問題轉成向量。",
        "向 Chroma 查詢 top 5 chunk。",
        "回傳 ids、documents、metadatas。",
    ])
    kv(doc, "交付物：", "retrieval.py 可執行。")
    kv(doc, "檢查點：", "精確 token 查詢（如 max_connections）大概率失敗。記錄這些失敗。")
    kv(doc, "Git commit：", "Phase 2: baseline dense retrieval")
    kv(doc, "AI 執行指令：", "此時不要加 BM25 或 reranker。保持 baseline 純淨。")

    doc.add_heading("Phase 3：生成 Baseline（1 天）", level=1)
    doc.add_paragraph("目標：產生附引用、會拒答的回答。")
    bullets(doc, [
        "撰寫 app/generation.py，提供 generate(question, chunk_ids, chunk_texts)。",
        "組 prompt，要求：只用給定上下文、以 [chunk_xxx] 引用 chunk id、找不到答案就拒答。",
        "呼叫 gemini-3.8-flash。",
        "回傳答案與被引用的 chunk id。",
    ])
    kv(doc, "交付物：", "generation.py 可執行。")
    kv(doc, "檢查點：", "回答中包含 [chunk_xxx]；不可回答的問題會觸發拒答。")
    kv(doc, "Git commit：", "Phase 3: generation with citation and refusal")
    kv(doc, "AI 執行指令：", "驗證模型輸出至少包含一個 chunk id。若沒有，標記 grounded=False。")

    doc.add_heading("Phase 4：FastAPI 服務化（1 天）", level=1)
    doc.add_paragraph("目標：將 RAG pipeline 暴露為 HTTP 服務。")
    bullets(doc, [
        "撰寫 app/main.py，提供 POST /ask。",
        "請求 body：{\"question\": \"...\"}",
        "回應：{\"answer\": \"...\", \"sources\": [...], \"grounded\": bool, \"latency_ms\": int}",
        "用 uvicorn app.main:app --reload 啟動。",
        "透過 http://127.0.0.1:8000/docs 測試。",
    ])
    kv(doc, "交付物：", "可用的 /ask 端點。")
    kv(doc, "檢查點：", "Swagger UI 能回傳合法 JSON。")
    kv(doc, "Git commit：", "Phase 4: FastAPI endpoint")
    kv(doc, "AI 執行指令：", "使用 Pydantic model 驗證請求。包含延遲測量。")

    doc.add_heading("Phase 5：評估（2–3 天）— 最關鍵", level=1)
    doc.add_paragraph("目標：量化系統品質並記錄失敗。")
    bullets(doc, [
        "建立 eval/test_set.json，共 30 題：10 正常題、10 精確 token 題、10 不可回答題。",
        "撰寫 eval/evaluate.py，計算 Recall@5、Grounding rate、正確拒答率、p95 延遲。",
        "找出 2–3 個具體失敗案例。",
        "撰寫 eval/EVAL.md，包含 baseline 指標與失敗分析。",
    ])
    kv(doc, "交付物：", "test_set.json、evaluate.py、EVAL.md。")
    kv(doc, "檢查點：", "你能說出「精確 token 題的 Recall@5 是 X，原因是 Y」。")
    kv(doc, "Git commit：", "Phase 5: evaluation - baseline Recall@5 = <X>")
    kv(doc, "AI 執行指令：", "評估期間不得修改檢索或生成邏輯。指標需按類別報告，不能只給總體。")

    doc.add_heading("Phase 6：Docker 化（0.5 天）", level=1)
    doc.add_paragraph("目標：讓服務可重現。")
    bullets(doc, [
        "撰寫 FastAPI 應用的 Dockerfile。",
        "本地 build 並 run。",
        "在 README 記錄指令。",
    ])
    kv(doc, "交付物：", "可用的 Docker image。")
    kv(doc, "檢查點：", "docker run -p 8000:8000 <image> 後服務可運行。")
    kv(doc, "Git commit：", "Phase 6: Dockerfile")
    kv(doc, "AI 執行指令：", "使用 python:3.11-slim。暴露 port 8000。不要把 .env 複製進 image；執行時用環境變數傳入。")

    doc.add_heading("Phase 7：部署（1–2 天）", level=1)
    doc.add_paragraph("目標：將後端部署到公開 URL。")
    bullets(doc, [
        "將 Docker image 推上 Hugging Face Spaces（Docker SDK）。",
        "驗證公開的 /docs 端點。",
        "可選：將 Open WebUI 部署到另一個 Space 或 Railway，並連到後端。",
        "確認：電腦關機後，服務仍可用。",
    ])
    kv(doc, "交付物：", "公開的 FastAPI URL。")
    kv(doc, "檢查點：", "用手機（不連家裡 Wi-Fi）能呼叫 /ask。")
    kv(doc, "Git commit：", "Phase 7: deployed to Hugging Face Spaces")
    kv(doc, "AI 執行指令：", "將 GEMINI_API_KEY 設為 Space secret。不要把 key commit 進去。")

    doc.add_heading("Phase 8：迭代 — 混合檢索（可選，2–3 天）", level=1)
    doc.add_paragraph("目標：用 BM25 + 向量融合改善檢索。")
    bullets(doc, [
        "對 chunk 文字建立 BM25 索引。",
        "用 Reciprocal Rank Fusion 合併向量 top-20 與 BM25 top-20。",
        "重跑 Phase 5 評估。",
        "更新 EVAL.md，加入 before/after 指標。",
    ])
    kv(doc, "交付物：", "更新後的 retrieval.py、更新後的 EVAL.md。")
    kv(doc, "檢查點：", "Recall@5 提升；失敗案例有解釋。")
    kv(doc, "Git commit：", "Phase 8: hybrid search - Recall@5 improved from <X> to <Y>")
    kv(doc, "AI 執行指令：", "生成模型保持不變。只能與 Phase 5 baseline 比較。")

    doc.add_heading("Phase 9：README 與履歷包裝（1 天）", level=1)
    doc.add_paragraph("目標：讓 repo 可理解、可放履歷。")
    bullets(doc, [
        "撰寫 README，包含：一句話說明、架構圖、如何運行（docker build / docker run / curl）、評估摘要、已知限制（2–3 項）。",
        "用指標寫出 4 行履歷 bullet。",
        "清理 repo（移除 notebook、確認無機密）。",
    ])
    kv(doc, "交付物：", "整理好的 GitHub repo 與履歷 bullet。")
    kv(doc, "檢查點：", "朋友只看 README 就能跑起專案。")
    kv(doc, "Git commit：", "Phase 9: README and project polish")
    kv(doc, "AI 執行指令：", "確保 README 包含 Phase 7 的 live demo URL。")

    doc.add_heading("依賴關係圖", level=1)
    code_block(doc,
        "Phase -1 [done] -> Phase 0 [done] -> Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 -> Phase 6 -> Phase 7\n"
        "                                        \\           /\n"
        "                                         Phase 5 <-\n"
        "                                            |\n"
        "                                         Phase 8 (optional)\n"
        "                                            |\n"
        "                                         Phase 9"
    )
    kv(doc, "規則：", "Phase 5 必須在 Phase 7 之前完成。評估數字是 README 與履歷的必要素材。")

    doc.add_heading("每個 Phase 結束後的固定 Git 流程", level=1)
    code_block(doc, "git add .\ngit commit -m \"Phase N: <description>\"\ngit push")

    doc.save("RAG_Project_Plan_ZH.docx")
    print("Saved: RAG_Project_Plan_ZH.docx")


# ---------- main ----------

if __name__ == "__main__":
    build_en()
    build_zh()
    print("Done. Both files generated.")