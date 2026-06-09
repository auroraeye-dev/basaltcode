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

def search_documents(query: str, top_k: int = 5) -> list[dict]:
    query_embedding = get_embedding(query)
    
    result = supabase.rpc("match_chunks", {
        "query_embedding": query_embedding,
        "match_count": top_k
    }).execute()
    
    return result.data if result.data else []

def format_context(chunks: list[dict]) -> str:
    context = ""
    for chunk in chunks:
        source = chunk.get("metadata", {}).get("filename", "unknown")
        content = chunk.get("content", "")
        context += f"\n[Source: {source}]\n{content}\n"
    return context
