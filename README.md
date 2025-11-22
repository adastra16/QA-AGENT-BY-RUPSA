QA-Agent – Automated Testcase & Script Generator

This project was created by Rupsa Nanda, and this is the assignment assigned to me.
It automates testcase generation from uploaded documents and also generates Selenium scripts based on selected testcases.

The backend is built using FastAPI, the UI is in Streamlit, and ChromaDB stores the knowledge base.

Features

Upload multiple project/support documents

Build a knowledge base

Generate structured test cases

View and select previously generated test cases

Auto-generate Selenium scripts from a testcase

Tech Stack

Python 3.10

FastAPI

Streamlit

ChromaDB

SentenceTransformer

Selenium WebDriver

How to Run
1. Start Backend
uvicorn backend.main:app --reload --port 8000

2. Start Streamlit UI
streamlit run ui/app.py


Backend: http://127.0.0.1:8000
UI: http://localhost:8501

Steps to Use

Open the Streamlit UI

Upload your documents

Click Build KB

Enter requirement text

Generate testcases

Refresh testcases

Select one

Generate Selenium script

Project Structure
backend/
ui/
uploaded_assets/
generated_testcases.json

Final Note

Thank you for checking this project.