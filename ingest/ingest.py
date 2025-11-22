import os
from pathlib import Path

def load_documents(folder="uploaded_docs"):
    docs = []
    folder_path = Path(folder)

    for file in folder_path.iterdir():
        if file.suffix in [".txt", ".md", ".json", ".html"]:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                docs.append(f.read())
        elif file.suffix == ".pdf":
            # placeholder for PDF extraction
            docs.append("PDF content goes here")
        else:
            print(f"Skipping unsupported file: {file}")

    return docs

if __name__ == "__main__":
    documents = load_documents()
    print(f"Loaded {len(documents)} documents.")
