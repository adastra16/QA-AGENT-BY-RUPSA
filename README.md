# QA-Agent – Automated Testcase & Selenium Script Generator

**Created by:** Rupsa Nanda  
**Assignment Project**

QA-Agent is an intelligent automated QA workflow tool. It generates testcases from uploaded documents and converts selected testcases into Selenium scripts. The system builds its own knowledge base using ChromaDB and uses an LLM-based embedding model for understanding document content.

---

## Project Components
- FastAPI backend  
- Streamlit UI  
- ChromaDB vector storage  
- SentenceTransformer embeddings  
- Automated Selenium script generator  

---

## Features
1. Upload multiple project/support documents  
2. Build a searchable knowledge base using ChromaDB  
3. Generate structured test cases automatically  
4. View previously generated test cases  
5. Select a testcase and generate Selenium automation scripts  
6. Simple UI built with Streamlit  
7. Fast backend powered by FastAPI  

---

## Tech Stack
- Python 3.10  
- FastAPI  
- Streamlit  
- ChromaDB  
- SentenceTransformer  
- Selenium WebDriver  
- Uvicorn  

---

## Project Structure
QA-AGENT/
│
├── backend/
│ ├── main.py
│ ├── requirements.txt
│ └── ...other backend modules
│
├── ui/
│ ├── app.py
│ └── ...UI components
│
├── uploaded_assets/ # Stores uploaded documents
├── generated_testcases.json # Saved testcases
└── README.md

---

## How to Run the Project Locally

### 1. Start the Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
Backend runs at:  
**http://127.0.0.1:8000**

API documentation:  
**http://127.0.0.1:8000/docs**

---

### 2. Start the Streamlit UI
cd ui
streamlit run app.py
UI runs at:  
**http://localhost:8501**

---

## Steps to Use QA-Agent
1. Open the Streamlit UI  
2. Upload one or more documents  
3. Click **Build KB** to create the knowledge base  
4. Enter requirement text  
5. Click **Generate Testcases**  
6. Click **Refresh Testcases**  
7. Select a testcase  
8. Click **Generate Selenium Script**  

---

## Notes
- ChromaDB stores embeddings locally inside the project folder.  
- Generated testcases persist in `generated_testcases.json`.  
- Selenium scripts are generated directly from the testcase structure.  

---

## Final Note
Thank you for reviewing this assignment project.  
QA-Agent demonstrates how automation and embeddings can streamline QA workflows and reduce manual effort.
