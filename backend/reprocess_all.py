import os
import base64
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
import pypdf
import fitz

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

CHUNK_SIZE = 500
CHUNK_OVERLAP = 120
MIN_WIDTH = 280
MIN_HEIGHT = 200

# Same metadata map as ingest.py (CPwE excluded — we keep it as-is)
DOC_METADATA = {
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

def get_embedding(text: str):
    return client.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        chunks.append(" ".join(words[start:start+size]))
        start += size - overlap
    return chunks

def extract_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        for page in pypdf.PdfReader(f).pages:
            t = page.extract_text()
            if t: text += t + "\n"
    return text

VISION_PROMPT = """You are an expert architecture analyst. This image is from an industrial/IT standards document.
If it contains ANY technical/architectural content (network topology, architecture diagram, zone model, device layout, protocol flow, reference architecture, data flow), describe it in dense detail: zones/levels and their order, every component/device with exact product names, how things connect (firewalls, DMZ, gateways), protocols/ports, security controls.
ONLY respond "SKIP" if it is purely a logo, decorative photo, or cover graphic with no technical content. When in doubt, DESCRIBE."""

def describe_image(image_bytes):
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": VISION_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
        ]}],
        max_tokens=900, temperature=0.2
    )
    return resp.choices[0].message.content.strip()

def get_doc_id(filename, source):
    existing = supabase.table("documents").select("id").eq("name", filename).execute()
    if existing.data:
        return existing.data[0]["id"]
    return supabase.table("documents").insert({"name": filename, "source": source}).execute().data[0]["id"]

def reprocess(pdf_path):
    filename = os.path.basename(pdf_path)
    if filename == "CPwE.pdf":
        print(f"Skipping CPwE (keep as-is)")
        return
    meta = DOC_METADATA.get(filename)
    if not meta:
        print(f"No metadata for {filename}, skipping")
        return

    print(f"\n=== {filename} ({meta['standard']}) ===")
    doc_id = get_doc_id(filename, meta["standard"])

    # 1. Delete old text chunks (keep nothing stale), but NOT diagram_descriptions
    supabase.table("document_chunks").delete().eq("document_id", doc_id).neq("metadata->>type", "diagram_description").execute()
    # also delete rows with no type field (old chunks)
    print("  Cleared old text chunks")

    # 2. Re-chunk text with metadata
    text = extract_text(pdf_path)
    chunks = chunk_text(text)
    print(f"  Re-chunking {len(chunks)} text chunks...")
    for i, chunk in enumerate(chunks):
        if not chunk.strip(): continue
        emb = get_embedding(chunk)
        supabase.table("document_chunks").insert({
            "document_id": doc_id, "content": chunk, "embedding": emb,
            "metadata": {"chunk_index": i, "filename": filename, "source": meta["standard"],
                         "domains": meta["domains"], "vendor": meta["vendor"],
                         "standard": meta["standard"], "doc_type": meta["doc_type"], "type": "text"}
        }).execute()
    print(f"  Text done ({len(chunks)} chunks)")

    # 3. Extract images via vision
    doc = fitz.open(pdf_path)
    seen = set()
    stored = 0
    for page_num in range(len(doc)):
        for img in doc[page_num].get_images(full=True):
            xref = img[0]
            base = doc.extract_image(xref)
            if base.get("width",0) < MIN_WIDTH or base.get("height",0) < MIN_HEIGHT:
                continue
            h = hash(base["image"][:2000])
            if h in seen: continue
            seen.add(h)
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha > 3: pix = fitz.Pixmap(fitz.csRGB, pix)
                desc = describe_image(pix.tobytes("png"))
                if desc.strip().upper().startswith("SKIP"): continue
                emb = get_embedding(desc)
                supabase.table("document_chunks").insert({
                    "document_id": doc_id,
                    "content": f"[DIAGRAM from {meta['standard']} p{page_num+1}]\n{desc}",
                    "embedding": emb,
                    "metadata": {"filename": filename, "source": meta["standard"],
                                 "domains": meta["domains"], "type": "diagram_description", "page": page_num+1}
                }).execute()
                stored += 1
            except Exception as e:
                print(f"    img err p{page_num+1}: {e}")
    doc.close()
    print(f"  Diagrams stored: {stored}")

if __name__ == "__main__":
    docs_dir = os.path.join(os.path.dirname(__file__), "documents")
    pdfs = [f for f in os.listdir(docs_dir) if f.endswith(".pdf") and f != "CPwE.pdf"]
    print(f"Reprocessing {len(pdfs)} documents (CPwE excluded)")
    for p in pdfs:
        reprocess(os.path.join(docs_dir, p))
    print("\nALL DONE")