import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
import pypdf
import json

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with open(pdf_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def get_embedding(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def ingest_document(pdf_path: str, source_name: str = None):
    filename = os.path.basename(pdf_path)
    source = source_name or filename
    
    print(f"\nIngesting: {filename}")
    
    # check if already ingested
    existing = supabase.table("documents").select("id").eq("name", filename).execute()
    if existing.data:
        print(f"  Already ingested, skipping.")
        return

    # extract text
    print(f"  Extracting text...")
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        print(f"  No text found, skipping.")
        return
    print(f"  Extracted {len(text)} characters")

    # save document record
    doc_result = supabase.table("documents").insert({
        "name": filename,
        "source": source
    }).execute()
    doc_id = doc_result.data[0]["id"]
    print(f"  Document ID: {doc_id}")

    # chunk text
    chunks = chunk_text(text)
    print(f"  Created {len(chunks)} chunks")

    # embed and store each chunk
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        
        embedding = get_embedding(chunk)
        
        supabase.table("document_chunks").insert({
            "document_id": doc_id,
            "content": chunk,
            "embedding": embedding,
            "metadata": {"chunk_index": i, "source": source, "filename": filename}
        }).execute()
        
        if (i + 1) % 10 == 0:
            print(f"  Stored {i + 1}/{len(chunks)} chunks...")

    print(f"  Done. {len(chunks)} chunks stored.")

def ingest_all(documents_folder: str):
    pdfs = [f for f in os.listdir(documents_folder) if f.endswith(".pdf")]
    
    skip = ["Satvik_Mishra_Novartis_HealthIntelligence.pdf"]
    pdfs = [p for p in pdfs if p not in skip]
    
    print(f"Found {len(pdfs)} PDFs to ingest")
    
    for pdf_file in pdfs:
        full_path = os.path.join(documents_folder, pdf_file)
        ingest_document(full_path)
    
    print("\nAll documents ingested.")

if __name__ == "__main__":
    documents_dir = os.path.join(os.path.dirname(__file__), "documents")
    ingest_all(documents_dir)