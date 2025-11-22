# backend/main.py
import os
import json
import uuid
import logging
from typing import List, Dict

from fastapi import FastAPI, UploadFile, File, Body
from pydantic import BaseModel

# ChromaDB
from chromadb import PersistentClient

# Embedding model
from sentence_transformers import SentenceTransformer

# Text splitting
from langchain_text_splitters import RecursiveCharacterTextSplitter

# HTML parsing
from bs4 import BeautifulSoup

# ================================
# Logging
# ================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qa-agent")

CHROMA_DIR = "chroma_db"
os.makedirs(CHROMA_DIR, exist_ok=True)

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

# ================================
# Chroma client
# ================================
client = PersistentClient(path=CHROMA_DIR)

collection_name = "qa_agent_docs"
try:
    collection = client.get_collection(collection_name)
    logger.info(f"Loaded collection '{collection_name}'")
except Exception:
    collection = client.create_collection(collection_name)
    logger.info(f"Created collection '{collection_name}'")

# ================================
# Embedding model
# ================================
embed_model = SentenceTransformer(EMBED_MODEL_NAME)

# ================================
# FastAPI App
# ================================
app = FastAPI(title="QA-Agent Backend")

# ================================
# Persistent Testcase Storage
# ================================
TESTCASE_FILE = "generated_testcases.json"

if os.path.exists(TESTCASE_FILE):
    try:
        with open(TESTCASE_FILE, "r") as f:
            GENERATED_TESTCASES = json.load(f)
    except:
        GENERATED_TESTCASES = {}
else:
    GENERATED_TESTCASES = {}

def save_testcases():
    with open(TESTCASE_FILE, "w") as f:
        json.dump(GENERATED_TESTCASES, f, indent=2)


# ================================
# Helper: Extract Text
# ================================
def extract_text_from_file(filename: str, bytes_data: bytes) -> str:
    name = filename.lower()
    text = ""

    try:
        if name.endswith(".html"):
            soup = BeautifulSoup(bytes_data.decode("utf-8", errors="ignore"), "html.parser")
            text = soup.get_text(separator="\n")

            elements = []
            for el in soup.find_all(True):
                attrs = {k: v for k, v in el.attrs.items()
                         if k in ("id", "name", "class", "type", "placeholder")}
                if attrs:
                    elements.append(f"<{el.name}> attrs={attrs} text={el.get_text().strip()[:60]}")

            if elements:
                text += "\n\nHTML_ELEMENTS:\n" + "\n".join(elements)

        elif name.endswith((".md", ".txt", ".json")):
            text = bytes_data.decode("utf-8", errors="ignore")

        elif name.endswith(".pdf"):
            try:
                import fitz
                doc = fitz.open(stream=bytes_data, filetype="pdf")
                pages = [p.get_text() for p in doc]
                text = "\n".join(pages)
            except:
                text = ""

        else:
            text = bytes_data.decode("utf-8", errors="ignore")

    except Exception:
        text = ""

    return text


# ================================
# Upload Files API
# ================================
@app.post("/upload_files/")
async def upload_files(files: List[UploadFile] = File(...)):
    saved = []
    upload_dir = "uploaded_assets"
    os.makedirs(upload_dir, exist_ok=True)

    for f in files:
        path = os.path.join(upload_dir, f.filename)
        data = await f.read()
        with open(path, "wb") as fh:
            fh.write(data)
        saved.append({"filename": f.filename, "path": path})

    return {"status": "ok", "saved": saved}


# ================================
# Build Knowledge Base
# ================================
@app.post("/build_kb/")
async def build_kb(
    file_paths: List[str] = Body(...),
    chunk_size: int = Body(1000),
    chunk_overlap: int = Body(200)
):
    logger.info(f"[build_kb] Received file paths: {file_paths}")

    docs = []
    metadatas = []
    ids = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    for path in file_paths:
        if not os.path.exists(path):
            logger.warning(f"[build_kb] Missing file: {path}")
            continue

        with open(path, "rb") as f:
            raw = f.read()

        text = extract_text_from_file(path, raw)
        if not text:
            logger.warning(f"[build_kb] No text extracted: {path}")
            continue

        chunks = splitter.split_text(text)

        for idx, chunk in enumerate(chunks):
            uid = str(uuid.uuid4())

            docs.append(chunk)
            metadatas.append({
                "source": os.path.basename(path),
                "path": path,
                "chunk_index": idx
            })
            ids.append(uid)

    if not docs:
        return {"status": "no_docs_found", "received": file_paths}

    embeddings = embed_model.encode(docs, convert_to_numpy=True).tolist()

    collection.add(
        documents=docs,
        ids=ids,
        metadatas=metadatas,
        embeddings=embeddings
    )

    return {
        "status": "kb_built",
        "num_chunks": len(docs),
        "ingested_files": list({m["source"] for m in metadatas})
    }


# ================================
# Testcase Generation
# ================================
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/generate_testcases/")
async def generate_testcases(req: QueryRequest):
    result = collection.query(
        query_texts=[req.query],
        n_results=req.top_k
    )

    if not result.get("documents") or not result["documents"][0]:
        return {"status": "ok", "generated": [], "retrieved": 0}

    retrieved_docs = []
    for text, meta in zip(result["documents"][0], result["metadatas"][0]):
        retrieved_docs.append({"text": text, "meta": meta})

    # Simple rule-based testcase generator
    testcases = []

    for idx, item in enumerate(retrieved_docs, start=1):
        tc = {
            "Test_ID": f"TC-{idx:03}",
            "Feature": "Checkout Flow",
            "Test_Scenario": f"Validate: {req.query}",
            "Expected_Result": "Checkout should function correctly.",
            "Grounded_In": [item["meta"].get("source", "unknown")]
        }
        key = str(uuid.uuid4())
        GENERATED_TESTCASES[key] = {"id": key, "payload": tc}
        testcases.append({"id": key, "payload": tc})

    save_testcases()

    return {"status": "ok", "generated": testcases, "retrieved": len(retrieved_docs)}


# ================================
# List Testcases
# ================================
@app.get("/list_testcases/")
async def list_testcases():
    return {
        "count": len(GENERATED_TESTCASES),
        "items": list(GENERATED_TESTCASES.values())
    }
# ================================
# Generate Selenium Script
# ================================

class SeleniumRequest(BaseModel):
    testcase_id: str

@app.post("/generate_selenium_script/")
async def generate_selenium_script(req: SeleniumRequest):
    tc = GENERATED_TESTCASES.get(req.testcase_id)
    if not tc:
        return {"error": "testcase_not_found"}

    testcase = tc["payload"]

    # Simple static selenium script (no GPT)
    script = f"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get("http://example.com/checkout")

print("Running Testcase: {testcase['Test_ID']}")

# NOTE: This is a placeholder script because no DOM is loaded.
# Replace selectors with the real page selectors.

try:
    print("Test Scenario: {testcase['Test_Scenario']}")
    print("Expected: {testcase['Expected_Result']}")

    # Example wait
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("✓ Page loaded successfully")

except Exception as e:
    print("✗ Test failed:", e)

driver.quit()
"""

    return {"status": "ok", "script": script}
