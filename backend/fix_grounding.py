import re

path = "/Users/SatvikMishra/Desktop/basaltcode/backend/diagram_generator.py"
with open(path) as f:
    content = f.read()

# 1. Replace SYSTEM_PROMPT with a grounding-first version
new_system = '''SYSTEM_PROMPT = """You are an expert industrial and enterprise architecture designer.
Your job is to generate architecture diagrams as structured JSON, GROUNDED in the reference documents provided.

CRITICAL GROUNDING RULES:
- The REFERENCE CONTEXT contains real architecture diagrams and specifications extracted from authoritative standards documents (CPwE, NIST, IEC 62443, Cisco, etc.)
- You MUST prefer component names, products, zone structures, protocols, and topology found in the REFERENCE CONTEXT over your own general knowledge
- When the reference context names a specific product (e.g. "Cisco Stratix 5700", "Allen-Bradley ControlLogix", "FactoryTalk"), USE THAT EXACT NAME
- When the reference context shows a zone/level structure, MIRROR that structure
- When the reference context labels protocols/ports, USE those exact labels
- Only fall back to general knowledge for components genuinely not covered by the references

You have access to {icon_count} icons. Use ONLY these icon keys (pick the most appropriate):
{icon_sample}

RULES:
1. Every node MUST have an icon key from the list above
2. Prefer real product names from the REFERENCE CONTEXT, then domain knowledge
3. Group nodes into zones that match the reference architecture structure
4. Every edge must have a label showing the protocol or relationship (use reference protocols)
5. Follow the domain rules provided exactly
6. Output ONLY valid JSON, no explanation, no markdown

OUTPUT FORMAT:
{{
  "title": "Architecture title",
  "nodes": [
    {{
      "id": "unique_id",
      "label": "Component Name",
      "icon": "namespace::IconName",
      "zone": "zone_id",
      "description": "What this does, why it is here, and which standard/document supports it"
    }}
  ],
  "edges": [
    {{
      "id": "edge_id",
      "from": "node_id",
      "to": "node_id",
      "label": "Protocol or relationship",
      "style": "solid or dashed"
    }}
  ],
  "zones": [
    {{
      "id": "zone_id",
      "label": "Zone Label",
      "type": "cloud or onprem or dmz or safety or enterprise",
      "color": "blue or grey or orange or red or purple",
      "nodes": ["node_id_list"]
    }}
  ]
}}"""'''

content = re.sub(r'SYSTEM_PROMPT = """.*?"""', new_system, content, count=1, flags=re.DOTALL)

# 2. Restructure user_message — reference context FIRST, framed as authoritative
old_user = re.search(r'    user_message = f""".*?Every node must have a real icon key from the list provided\."""', content, flags=re.DOTALL)
if old_user:
    new_user = '''    user_message = f"""REFERENCE CONTEXT — real architecture knowledge extracted from authoritative standards documents and their diagrams. Build the architecture from THIS:
========================================================
{rag_context}
========================================================

Now generate an architecture diagram for this request:
"{prompt}"

DOMAIN: {domain.upper()}
CLOUD: {classified.get('cloud', 'aws')}
COMPLIANCE: {', '.join(classified.get('compliance', []))}

DOMAIN STRUCTURE RULES (follow exactly):
{domain_rules}

INSTRUCTIONS:
- Build the architecture primarily from the REFERENCE CONTEXT above — use its exact product names, zone structures, and protocols
- Fill any gaps with the domain rules and standard industry knowledge
- Include all components needed for a complete, production-grade system
- Every node must have a real icon key from the provided list
- In each node description, note which standard or document supports that choice when possible
Output ONLY the JSON."""'''
    content = content[:old_user.start()] + new_user + content[old_user.end():]
    print("user_message replaced")
else:
    print("WARNING: user_message not found")

# 3. Upgrade model to gpt-4o for generation
content = content.replace('model="gpt-4o-mini",\n        messages=[\n            {"role": "system", "content": system}', 'model="gpt-4o",\n        messages=[\n            {"role": "system", "content": system}')

with open(path, "w") as f:
    f.write(content)
print("DONE")   