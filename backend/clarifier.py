"""
Clarification layer: decides whether a prompt has enough detail to produce a
great architecture diagram. If not, returns targeted free-text questions.
Only interrupts when genuinely needed (smart detection).
"""
import os, json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CLARIFY_PROMPT = """You are a senior solutions architect. Decide whether a design request already has enough detail to produce a strong architecture diagram.

DEFAULT TO "ready". Most requests are good enough — a competent architect fills reasonable defaults (standard HA, sensible DB choice, typical security). Only ask questions when the prompt is genuinely SPARSE and missing something that would fundamentally change the shape of the diagram.

Mark "ready" (DO NOT ask) when the prompt already includes any reasonable combination of: the domain/system type, the main components or production areas, OR a compliance/standard. 
Examples of READY prompts (do not question these):
- "OT network for automotive plant with CPwE, body shop paint shop and assembly, IEC 62443" -> READY (has domain, cells, compliance)
- "Scalable web application on AWS with high availability and WAF" -> READY (has platform, scale, key components)
- "Pharma manufacturing system with 21 CFR Part 11 and GAMP5" -> READY

Mark "needs_info" ONLY when the prompt is a bare fragment with no specifics, e.g.:
- "web app on AWS" -> needs_info (no scale, no data, no purpose)
- "make me an OT network" -> needs_info (no industry, no components)
- "cloud system" -> needs_info

When you do ask, ask only 2-3 questions, and only about the MOST critical missing pieces.

Return STRICT JSON, no markdown:
{
  "status": "ready" | "needs_info",
  "questions": [ {"q": "short question", "why": "one-line reason"} ]
}
If "ready", questions = []."""

def clarify(prompt: str) -> dict:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": CLARIFY_PROMPT},
                {"role": "user", "content": f"Design request: \"{prompt}\"\n\nDecide if this is ready or needs clarification."}
            ],
            max_tokens=500,
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        if data.get("status") not in ("ready", "needs_info"):
            return {"status": "ready", "questions": []}
        # safety: cap at 4 questions
        data["questions"] = (data.get("questions") or [])[:4]
        return data
    except Exception as e:
        # On any failure, don't block the user — just proceed to generate
        return {"status": "ready", "questions": [], "error": str(e)}

def merge_answers(prompt: str, qa_pairs: list) -> str:
    """Combine original prompt with the user's clarifying answers into one enriched prompt."""
    if not qa_pairs:
        return prompt
    extra = "\n".join(f"- {p.get('q','')}: {p.get('a','')}" for p in qa_pairs if p.get('a'))
    if not extra.strip():
        return prompt
    return f"{prompt}\n\nAdditional requirements clarified by the user:\n{extra}"