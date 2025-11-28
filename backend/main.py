
import os
import json
import uuid
import logging
from typing import List, Dict

from fastapi import FastAPI, UploadFile, File, Body
from pydantic import BaseModel

from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="QA-Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # use specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qa-agent")


CHROMA_DIR = "chroma_db"
os.makedirs(CHROMA_DIR, exist_ok=True)

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

client = PersistentClient(path=CHROMA_DIR)
collection_name = "qa_agent_docs"

try:
    collection = client.get_collection(collection_name)
    logger.info(f"Loaded collection '{collection_name}'")
except Exception:
    collection = client.create_collection(collection_name)
    logger.info(f"Created collection '{collection_name}'")

# Lazy load embedding model to save memory
_embed_model = None

def get_embed_model():
    global _embed_model
    if _embed_model is None:
        logger.info("Loading embedding model...")
        _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    return _embed_model



TESTCASE_FILE = "generated_testcases.json"
if os.path.exists(TESTCASE_FILE):
    try:
        with open(TESTCASE_FILE, "r", encoding="utf-8") as f:
            GENERATED_TESTCASES = json.load(f)
    except Exception:
        GENERATED_TESTCASES = {}
else:
    GENERATED_TESTCASES = {}


def save_testcases():
    with open(TESTCASE_FILE, "w", encoding="utf-8") as f:
        json.dump(GENERATED_TESTCASES, f, indent=2)


def extract_text_from_file(filename: str, bytes_data: bytes) -> str:
    name = filename.lower()

    try:
        if name.endswith(".html") or name.endswith(".htm"):
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

            return text

        if name.endswith((".md", ".txt", ".json")):
            return bytes_data.decode("utf-8", errors="ignore")

        if name.endswith(".pdf"):
            try:
                import fitz
                doc = fitz.open(stream=bytes_data, filetype="pdf")
                return "\n".join([p.get_text() for p in doc])
            except:
                return ""

        return bytes_data.decode("utf-8", errors="ignore")

    except:
        return ""



@app.get("/")
async def root():
    return {"status": "ok", "message": "QA-Agent Backend is running"}

@app.get("/health")
async def health():
    try:
        # Check if ChromaDB is accessible
        collection_count = collection.count()
        return {
            "status": "healthy", 
            "service": "qa-agent-backend",
            "chromadb_documents": collection_count,
            "embedding_model_loaded": _embed_model is not None
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "qa-agent-backend",
            "error": str(e)
        }

@app.post("/upload_files/")
async def upload_files(files: List[UploadFile] = File(...)):
    try:
        saved = []
        upload_dir = "uploaded_assets"
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
        
        # Create upload directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"Upload directory: {os.path.abspath(upload_dir)}")

        for f in files:
            try:
                if not f.filename:
                    logger.warning("Received file with no filename")
                    continue
                
                # Sanitize filename to prevent path traversal
                safe_filename = os.path.basename(f.filename)
                path = os.path.join(upload_dir, safe_filename)
                
                # Read file content
                content = await f.read()
                
                # Check file size
                if len(content) > MAX_FILE_SIZE:
                    logger.warning(f"File {f.filename} too large: {len(content)} bytes")
                    return {"status": "error", "message": f"File {f.filename} is too large (max 10MB)"}
                
                # Write file
                with open(path, "wb") as fh:
                    fh.write(content)
                
                saved.append({"filename": safe_filename, "path": path, "size": len(content)})
                logger.info(f"Saved file: {path} ({len(content)} bytes)")
                
            except Exception as e:
                logger.error(f"Error saving file {f.filename}: {str(e)}")
                return {"status": "error", "message": f"Failed to save {f.filename}: {str(e)}"}

        if not saved:
            return {"status": "error", "message": "No files were saved"}

        return {"status": "ok", "saved": saved}
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Upload failed: {str(e)}"}



@app.post("/build_kb/")
async def build_kb(
    file_paths: List[str] = Body(...),
    chunk_size: int = Body(1000),
    chunk_overlap: int = Body(200)
):
    try:
        docs = []
        metadatas = []
        ids = []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

        for raw_path in file_paths:
            try:
                # Normalize path separators
                path = raw_path.replace("/", os.sep).replace("\\", os.sep)
                
                # Check if file exists
                if not os.path.exists(path):
                    logger.warning(f"Missing file: {path} (absolute: {os.path.abspath(path)})")
                    continue

                logger.info(f"Processing file: {path}")

                with open(path, "rb") as f:
                    content = f.read()

                text = extract_text_from_file(path, content)
                if not text:
                    logger.warning(f"No text extracted from: {path}")
                    continue

                chunks = splitter.split_text(text)
                logger.info(f"Split {path} into {len(chunks)} chunks")

                for i, c in enumerate(chunks):
                    uid = str(uuid.uuid4())
                    docs.append(c)
                    metadatas.append({"source": os.path.basename(path), "path": path, "chunk_index": i})
                    ids.append(uid)
                    
            except Exception as e:
                logger.error(f"Error processing file {raw_path}: {str(e)}")
                continue

        if not docs:
            return {"status": "no_docs_found", "received": file_paths, "message": "No documents could be processed"}

        # Process in batches to avoid memory issues
        BATCH_SIZE = 50  # Process 50 chunks at a time
        logger.info(f"Generating embeddings for {len(docs)} chunks in batches of {BATCH_SIZE}...")
        
        try:
            embed_model = get_embed_model()
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            return {"status": "error", "message": f"Failed to load embedding model: {str(e)}"}

        # Process in batches
        for i in range(0, len(docs), BATCH_SIZE):
            batch_docs = docs[i:i+BATCH_SIZE]
            batch_metadatas = metadatas[i:i+BATCH_SIZE]
            batch_ids = ids[i:i+BATCH_SIZE]
            
            try:
                logger.info(f"Processing batch {i//BATCH_SIZE + 1}/{(len(docs)-1)//BATCH_SIZE + 1} ({len(batch_docs)} chunks)...")
                batch_embeddings = embed_model.encode(batch_docs, convert_to_numpy=True, show_progress_bar=False)
                
                try:
                    collection.add(
                        documents=batch_docs,
                        metadatas=batch_metadatas,
                        ids=batch_ids,
                        embeddings=batch_embeddings.tolist()
                    )
                except Exception as e:
                    logger.warning(f"Error with tolist(), trying without: {str(e)}")
                    collection.add(
                        documents=batch_docs,
                        metadatas=batch_metadatas,
                        ids=batch_ids,
                        embeddings=batch_embeddings
                    )
                    
            except MemoryError:
                logger.error("Out of memory while processing embeddings")
                return {"status": "error", "message": "Out of memory. Try uploading smaller files or reduce chunk_size."}
            except Exception as e:
                logger.error(f"Error processing batch: {str(e)}")
                return {"status": "error", "message": f"Error processing batch: {str(e)}"}

        return {
            "status": "kb_built",
            "num_chunks": len(docs),
            "ingested_files": list({m["source"] for m in metadatas})
        }
    
    except Exception as e:
        logger.error(f"Build KB error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Failed to build KB: {str(e)}"}


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/generate_testcases/")
async def generate_testcases(req: QueryRequest):
    try:
        result = collection.query(
            query_texts=[req.query],
            n_results=req.top_k
        )
    except Exception as e:
        return {"status": "error", "details": str(e)}

    retrieved = []
    try:
        for t, meta in zip(result["documents"][0], result["metadatas"][0]):
            retrieved.append({"text": t, "meta": meta})
    except:
        retrieved = []

    generated = []

    for i, item in enumerate(retrieved, start=1):
        tc = {
            "Test_ID": f"TC-{i:03}",
            "Feature": req.query,
            "Test_Scenario": f"Validate: {req.query}",
            "Expected_Result": "The feature should work as expected.",
            "Grounded_In": [item["meta"].get("source", "unknown")],
        }

        uid = str(uuid.uuid4())
        GENERATED_TESTCASES[uid] = {"id": uid, "payload": tc}
        generated.append({"id": uid, "payload": tc})

    save_testcases()
    return {"status": "ok", "generated": generated, "retrieved": len(retrieved)}



@app.get("/list_testcases/")
async def list_testcases():
    return {"count": len(GENERATED_TESTCASES), "items": list(GENERATED_TESTCASES.values())}


class SeleniumRequest(BaseModel):
    testcase_id: str


@app.post("/generate_selenium_script/")
async def generate_selenium_script(req: SeleniumRequest):
    tc = GENERATED_TESTCASES.get(req.testcase_id)
    if not tc:
        return {"error": "testcase_not_found"}

    testcase = tc["payload"]

    script = f"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get("http://example.com/checkout")

print("Running Testcase: {testcase['Test_ID']}")
print("Scenario: {testcase['Test_Scenario']}")
print("Expected: {testcase['Expected_Result']}")

WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

driver.quit()
""".strip()

    return {"status": "ok", "selenium_script": script}
