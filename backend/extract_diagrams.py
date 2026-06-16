import os
import base64
import json
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
import fitz

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Lower threshold — capture more
MIN_WIDTH = 280
MIN_HEIGHT = 200

VISION_PROMPT = """You are an expert industrial/OT architecture analyst analyzing an image from the Cisco/Rockwell CPwE (Converged Plantwide Ethernet) reference document.

Look carefully. Most images in this document ARE technical content: network topologies, architecture diagrams, zone/conduit models, device layouts, protocol flows, reference architectures, screenshots of configurations, or tables of components.

If the image contains ANY technical/architectural information, describe it in dense detail:
- Zones, levels, or layers shown (and their order top-to-bottom)
- Every component/device with EXACT product names (Cisco Stratix, Catalyst, Allen-Bradley ControlLogix, FactoryTalk, etc.)
- How things connect — switches, routers, firewalls, DMZ, gateways
- VLANs, interfaces, protocols, ports if labeled
- Security controls, segmentation, IES/IDMZ structure
- Any IP addressing or network design shown

Capture it as dense factual reference text an architecture AI can learn from.

ONLY respond "SKIP" if the image is purely: a company logo, a decorative photo of people/buildings, or a pure cover-page graphic with no technical content. When in doubt, DESCRIBE it — err heavily toward describing."""

def get_embedding(text: str):
    r = client.embeddings.create(model="text-embedding-3-small", input=text)
    return r.data[0].embedding

def describe_image(image_bytes: bytes) -> str:
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": VISION_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            ]
        }],
        max_tokens=900,
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()

def extract_and_describe(pdf_path: str, source_name: str, domains: list):
    filename = os.path.basename(pdf_path)
    print(f"\nExtracting from: {filename}")

    existing = supabase.table("documents").select("id").eq("name", filename).execute()
    doc_id = existing.data[0]["id"] if existing.data else \
        supabase.table("documents").insert({"name": filename, "source": source_name}).execute().data[0]["id"]

    # Delete previous diagram descriptions for this doc to avoid duplicates
    supabase.table("document_chunks").delete().eq("document_id", doc_id).eq("metadata->>type", "diagram_description").execute()
    print("  Cleared previous diagram descriptions")

    doc = fitz.open(pdf_path)
    stored = 0
    analyzed = 0
    seen_hashes = set()

    for page_num in range(len(doc)):
        page = doc[page_num]
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            width = base_image.get("width", 0)
            height = base_image.get("height", 0)

            if width < MIN_WIDTH or height < MIN_HEIGHT:
                continue

            # Dedup identical images (CPwE repeats the same figure across pages)
            img_hash = hash(base_image["image"][:2000])
            if img_hash in seen_hashes:
                continue
            seen_hashes.add(img_hash)

            analyzed += 1
            print(f"  p{page_num+1} img{img_index+1} ({width}x{height})... ", end="", flush=True)

            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                png_bytes = pix.tobytes("png")

                description = describe_image(png_bytes)

                if description.strip().upper().startswith("SKIP"):
                    print("skip")
                    continue

                embedding = get_embedding(description)
                supabase.table("document_chunks").insert({
                    "document_id": doc_id,
                    "content": f"[CPwE DIAGRAM p{page_num+1}]\n{description}",
                    "embedding": embedding,
                    "metadata": {
                        "source": source_name, "filename": filename,
                        "domains": domains, "type": "diagram_description",
                        "page": page_num + 1,
                    }
                }).execute()
                stored += 1
                print("STORED")
            except Exception as e:
                print(f"err: {e}")

    doc.close()
    print(f"\nDone. Analyzed {analyzed} unique images, stored {stored} descriptions.")

if __name__ == "__main__":
    docs_dir = os.path.join(os.path.dirname(__file__), "documents")
    extract_and_describe(os.path.join(docs_dir, "CPwE.pdf"), "CPwE", ["ot", "scada", "fmcg", "metal"])