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

CHUNK_SIZE = 500
CHUNK_OVERLAP = 120

# Map each document to its domain(s) and metadata.
# This is what makes retrieval precise — OT queries pull OT chunks only.
DOC_METADATA = {
    "CPwE.pdf": {"domains": ["ot", "scada", "fmcg", "metal"], "vendor": "Cisco/Rockwell", "standard": "CPwE", "doc_type": "reference_architecture"},
    "nist.sp.800-82r2.pdf": {"domains": ["ot", "scada"], "vendor": "NIST", "standard": "NIST SP 800-82", "doc_type": "standard"},
    "Whitepaper-Practical-Industrial-Control-System-Cybersecurity.pdf": {"domains": ["ot", "scada"], "vendor": "Generic", "standard": "ICS Security", "doc_type": "whitepaper"},
    "Survey_2024-ICS-OT-Cybersecurity_Opswat.pdf": {"domains": ["ot", "scada"], "vendor": "Opswat", "standard": "ICS Survey", "doc_type": "survey"},
    "b_ind_olh.pdf": {"domains": ["ot", "scada"], "vendor": "Cisco", "standard": "Industrial Network", "doc_type": "design_guide"},
    "NIST.CSWP.29.pdf": {"domains": ["ot", "general"], "vendor": "NIST", "standard": "NIST CSF", "doc_type": "framework"},
    "21-cfr-part-11-electronic-records-signatures-ai-gxp-compliance.pdf": {"domains": ["pharma"], "vendor": "FDA", "standard": "21 CFR Part 11", "doc_type": "regulation"},
    "gamp-5-computerized-system-validation-in-pharma.pdf": {"domains": ["pharma"], "vendor": "ISPE", "standard": "GAMP5", "doc_type": "standard"},
    "wellarchitected-framework.pdf": {"domains": ["general"], "vendor": "AWS", "standard": "Well-Architected", "doc_type": "framework"},
    "Architecture_and_Design.pdf": {"domains": ["general"], "vendor": "Generic", "standard": "Architecture", "doc_type": "guide"},
    "Infra_Topic_Paper_4-14_FINAL.pdf": {"domains": ["general", "ot"], "vendor": "Generic", "standard": "Infrastructure", "doc_type": "paper"},
}

def get_doc_metadata(filename: str) -> dict:
    return DOC_METADATA.get(filename, {"domains": ["general"], "vendor": "Unknown", "standard": "Unknown", "doc_type": "document"})

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
    meta = get_doc_metadata(filename)

    print(f"\nIngesting: {filename}")
    print(f"  Domains: {meta['domains']} | Standard: {meta['standard']}")

    existing = supabase.table("documents").select("id").eq("name", filename).execute()
    if existing.data:
        print(f"  Already ingested, skipping.")
        return

    print(f"  Extracting text...")
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        print(f"  No text found, skipping.")
        return
    print(f"  Extracted {len(text)} characters")

    doc_result = supabase.table("documents").insert({
        "name": filename,
        "source": source
    }).execute()
    doc_id = doc_result.data[0]["id"]
    print(f"  Document ID: {doc_id}")

    chunks = chunk_text(text)
    print(f"  Created {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue

        embedding = get_embedding(chunk)

        supabase.table("document_chunks").insert({
            "document_id": doc_id,
            "content": chunk,
            "embedding": embedding,
            "metadata": {
                "chunk_index": i,
                "source": source,
                "filename": filename,
                "domains": meta["domains"],
                "vendor": meta["vendor"],
                "standard": meta["standard"],
                "doc_type": meta["doc_type"],
            }
        }).execute()

        if (i + 1) % 25 == 0:
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