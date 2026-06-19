from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from diagram_generator import generate_diagram
load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from classifier import classify
from search import multi_search, search_documents, format_context

@app.get("/health")
def health():
    return {"status": "ok", "message": "Basalt backend running"}

@app.post("/parse")
async def parse_prompt(body: dict):
    prompt = body.get("prompt", "")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are an architecture requirements parser.
Extract structured information from the user's prompt and return ONLY valid JSON.
No explanation, no markdown, just raw JSON.

Return this exact structure:
{
  "app_type": "string (pharma/fmcg/ot/scada/metal/general)",
  "cloud": "string (aws/azure/gcp/hybrid/on-prem/unspecified)",
  "scale": "string (low/medium/high/unspecified)",
  "budget": "string (low/medium/high/unspecified)",
  "compliance": ["array of compliance requirements like FDA 21 CFR, GAMP5, IEC 62443 etc"],
  "region": "string or unspecified",
  "on_prem": false,
  "ambiguous_fields": ["fields that were not clear from the prompt"]
}"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)
    return {"status": "success", "parsed": parsed}

@app.post("/classify")
async def classify_prompt(body: dict):
    parsed = body.get("parsed", {})
    result = classify(parsed)
    return {"status": "success", "classified": result}

@app.post("/search")
async def search(body: dict):
    query = body.get("query", "")
    top_k = body.get("top_k", 5)
    chunks = search_documents(query, top_k)
    context = format_context(chunks)
    return {
        "status": "success",
        "chunks": chunks,
        "context": context
    }

from clarifier import clarify, merge_answers

@app.post("/clarify")
async def clarify_endpoint(body: dict):
    prompt = body.get("prompt", "")
    if not prompt.strip():
        return {"status": "ready", "questions": []}
    return clarify(prompt)

@app.post("/pipeline")
async def full_pipeline(body: dict):
    prompt = body.get("prompt", "")

    # step 1: parse
    parse_response = await parse_prompt({"prompt": prompt})
    parsed = parse_response["parsed"]

    # step 2: classify
    classify_response = await classify_prompt({"parsed": parsed})
    classified = classify_response["classified"]

    # step 3: search docs for relevant context
    search_query = f"{parsed.get('app_type')} {parsed.get('cloud')} architecture {' '.join(parsed.get('compliance', []))}"
    search_response = await search({"query": search_query, "top_k": 6})
    context = search_response["context"]

    return {
        "status": "success",
        "parsed": parsed,
        "classified": classified,
        "context_preview": context[:500],
        "message": "Pipeline stages 1-3 complete"
    }
@app.post("/generate")
async def generate(body: dict):
    prompt = body.get("prompt", "")
    # Merge any clarifying Q&A the user provided into the prompt
    qa_pairs = body.get("clarifications", [])
    if qa_pairs:
        from clarifier import merge_answers
        prompt = merge_answers(prompt, qa_pairs)

    # Step 1: parse
    parse_res = await parse_prompt({"prompt": prompt})
    parsed = parse_res["parsed"]

    # Step 2: classify
    classify_res = await classify_prompt({"parsed": parsed})
    classified = classify_res["classified"]
    domain = classified["app_type"]

    # Step 3: RAG search
    from search import multi_search, format_context
    chunks = multi_search(domain, parsed.get("compliance", []), top_k=4)
    rag_context = format_context(chunks)

    # Step 4: generate diagram
    result = generate_diagram(prompt, domain, classified, rag_context)
    from validator import main_validate
    if result.get("diagram"):
        result["diagram"] = main_validate(result["diagram"], domain)

    return {
        "status": result["status"],
        "parsed": parsed,
        "classified": classified,
        "diagram": result.get("diagram"),
        "error": result.get("error")
    }