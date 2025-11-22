
import json
from pathlib import Path


CHUNK_LEN = 800
CHUNK_OVERLAP = 100


OUTPUT_PATH = Path("ingest/chunks.json")


def split_into_chunks(text, size=CHUNK_LEN, overlap=CHUNK_OVERLAP):
    """Simple function to break long texts into overlapping chunks."""
    if not text:
        return []

    text = text.replace("\r\n", "\n")
    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = start + size
        chunk = text[start:end].strip()
        chunks.append(chunk)
        start += (size - overlap)

    return chunks


def prepare_chunks(upload_folder="uploaded_docs"):
    """Reads all files inside uploaded_docs and splits them into text chunks."""
    folder = Path(upload_folder)
    if not folder.exists():
        print("No uploaded files found.")
        return []

    all_data = []
    chunk_counter = 0

    for file in sorted(folder.iterdir()):
        try:
            content = file.read_text(encoding="utf-8", errors="ignore")
        except:
            content = ""

        if not content:
            continue

        pieces = split_into_chunks(content)
        for idx, part in enumerate(pieces):
            entry = {
                "id": f"chunk_{chunk_counter}",
                "source": file.name,
                "index": idx,
                "text": part
            }
            all_data.append(entry)
            chunk_counter += 1

    return all_data


if __name__ == "__main__":
    chunks = prepare_chunks()

    if not chunks:
        print("No chunks created.")
    else:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(chunks)} chunks to {OUTPUT_PATH}")
