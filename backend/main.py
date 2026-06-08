from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
import os
import json

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
  "app_type": "string (fintech/healthcare/ecommerce/saas/gaming/general)",
  "cloud": "string (aws/gcp/azure/hybrid/unspecified)",
  "scale": "string (low/medium/high/unspecified)",
  "budget": "string (low/medium/high/unspecified)",
  "compliance": ["array of compliance requirements like PCI-DSS, HIPAA etc"],
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