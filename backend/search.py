import os
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def search_documents(query: str, top_k: int = 5, domain: str = None) -> list[dict]:
    query_embedding = get_embedding(query)
    result = supabase.rpc("match_chunks", {
        "query_embedding": query_embedding,
        "match_count": top_k * 3 if domain else top_k
    }).execute()

    chunks = result.data if result.data else []

    # Domain filter — keep only chunks tagged for this domain
    if domain:
        filtered = []
        for c in chunks:
            domains = c.get("metadata", {}).get("domains", [])
            if domain in domains or "general" in domains:
                filtered.append(c)
        # prefer exact-domain chunks first
        exact = [c for c in filtered if domain in c.get("metadata", {}).get("domains", [])]
        rest = [c for c in filtered if domain not in c.get("metadata", {}).get("domains", [])]
        chunks = (exact + rest)[:top_k]

    return chunks

def multi_search(domain: str, compliance: list, top_k: int = 4) -> list[dict]:
    """Run several targeted searches and combine — richer context than one vague query."""
    queries = [
        f"{domain} architecture zones and network segmentation",
        f"{domain} components devices PLC SCADA controllers servers",
        f"{domain} protocols ports communication",
        f"{domain} security controls {' '.join(compliance)}",
    ]

    seen_ids = set()
    combined = []
    for q in queries:
        results = search_documents(q, top_k=top_k, domain=domain)
        for r in results:
            rid = r.get("id") or r.get("content", "")[:50]
            if rid not in seen_ids:
                seen_ids.add(rid)
                combined.append(r)
    return combined

def format_context(chunks: list[dict]) -> str:
    context = ""
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        source = meta.get("standard", meta.get("filename", "unknown"))
        content = chunk.get("content", "")
        context += f"\n[Source: {source}]\n{content}\n"
    return context