path = "/Users/SatvikMishra/Desktop/basaltcode/backend/clarifier.py"
with open(path) as f:
    content = f.read()

old = '''CLARIFY_PROMPT = """You are a senior solutions architect reviewing a request to design a system architecture.
Your job: decide whether the request has ENOUGH detail to produce an excellent, specific architecture diagram — or whether key information is missing.

Be pragmatic. Only ask questions when the missing info would MATERIALLY change the architecture. If the prompt is reasonably complete, say it is ready. Do not ask for nice-to-haves.

Consider what's missing that matters, e.g.:
- Scale / expected load (changes whether you need HA, autoscaling, load balancing)
- Data type & persistence (SQL vs NoSQL vs object storage)
- Public-facing vs internal
- High availability / multi-region needs
- Compliance requirements
- Integration points (on-prem systems, third parties)
- For industrial: which production areas/cells, which protocols, safety needs

Return STRICT JSON, no markdown:
{
  "status": "ready" | "needs_info",
  "questions": [
    {"q": "short clear question", "why": "one-line reason it matters for the design"}
  ]
}
If status is "ready", questions must be an empty array.
Ask at most 4 questions. Each must be answerable in a sentence. Only include questions whose answers would change the architecture."""'''

new = '''CLARIFY_PROMPT = """You are a senior solutions architect. Decide whether a design request already has enough detail to produce a strong architecture diagram.

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
If "ready", questions = []."""'''

if old in content:
    content = content.replace(old, new)
    print("clarifier prompt tightened")
else:
    print("WARNING: old prompt not found")

with open(path, "w") as f:
    f.write(content)
print("DONE")