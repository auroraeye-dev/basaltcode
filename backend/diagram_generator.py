import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from search import search_documents, format_context

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load icon registry
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "icons", "registry.json")
with open(REGISTRY_PATH) as f:
    ICON_REGISTRY = json.load(f)

ICON_KEYS = list(ICON_REGISTRY.keys())

DOMAIN_RULES = {
    "ot": """
- Always separate IT and OT with Industrial DMZ zone
- Use Purdue Model levels: Level 0 (Field), Level 1 (Machine Control), Level 2 (Supervisory), Level 3 (Site Operations), DMZ, Level 4 (Enterprise IT)
- Always include: OT Firewall, Jump Server, OPC-UA Gateway in DMZ
- Always include: SCADA, Historian at Level 2
- Always include: PLCs at Level 1
- Always include: Sensors/Actuators at Level 0
- Connect Level 2 to Level 3 via OPC-UA :4840
- Connect Level 1 to Level 2 via EtherNet/IP or Profinet
- No direct connection from Enterprise IT to OT without DMZ
- Use icon: industrial::OPC-UA Gateway for DMZ crossing
- Use icon: patterns::DMZ for DMZ zone
- Use icon: patterns::Purdue Model for reference
""",
    "pharma": """
- Always include validated system zones per GAMP5
- Always include audit trail capability (21 CFR Part 11)
- Always include electronic signature system
- Zones: Enterprise IT, Validated Systems, Lab Systems, Manufacturing
- Always include: QMS, MES, Historian
- All systems must have audit logging
- Use icon: security::Splunk or generic::SIEM for audit trail
""",
    "fmcg": """
- Use IEC 62443 Zone model: Zone 1 (Enterprise), Zone 2 (Supervisory), Zone 3 (Control/OT), Zone 4 (Safety SIS)
- Always include Industrial DMZ between Zone 1 and Zone 2
- Always include: SAP ERP in Zone 1, MES in Zone 2, PLCs in Zone 3
- Safety SIS must be air-gapped (Zone 4)
- Use data diode between Zone 2 and Zone 3
- Always include Historian in Zone 2
- Use OPC-UA for Zone 2 to Zone 3 communication
""",
    "metal": """
- Similar to OT but with MES and ERP integration
- Always include: Plant MES, Corporate ERP (SAP)
- Always include: Plant historian, SCADA
- Zones: Corporate IT, Plant Operations, Process Control, Field
- Include energy management systems
""",
    "scada": """
- Strict Purdue Model implementation
- Air gap or DMZ between IT and OT mandatory
- Always include: SCADA server, Historian, HMI, RTU/PLC
- Data diode for unidirectional data flow from OT to IT
- No internet access to SCADA network
- Include OT-specific SIEM (Claroty/Dragos/Nozomi)
""",
    "general": """
- Standard cloud architecture patterns
- Always include: Load Balancer, Compute, Database, Security, Monitoring
- Use AWS services where cloud is specified
- Include WAF for internet-facing applications
"""
}

SYSTEM_PROMPT = """You are an expert industrial and enterprise architecture designer.
Your job is to generate architecture diagrams as structured JSON.

You have access to {icon_count} icons. Use ONLY these icon keys (pick the most appropriate):
{icon_sample}

RULES:
1. Every node MUST have an icon key from the list above
2. Use real product names from the domain (Ignition SCADA, OSIsoft PI, Allen-Bradley PLC etc)
3. Group nodes into zones/groups that make architectural sense
4. Every edge must have a label showing the protocol or relationship
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
      "description": "What this component does and why it is here"
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
}}"""

def get_icon_sample(domain: str) -> str:
    relevant_prefixes = {
        "ot": ["industrial::", "scada::", "plc::", "cisco::", "security::", "patterns::", "aws::"],
        "pharma": ["aws::", "azure::", "security::", "generic::", "sap::"],
        "fmcg": ["industrial::", "scada::", "plc::", "sap::", "cisco::", "security::", "patterns::"],
        "scada": ["scada::", "industrial::", "plc::", "cisco::", "security::"],
        "metal": ["industrial::", "scada::", "plc::", "sap::", "cisco::"],
        "general": ["aws::", "azure::", "cisco::", "generic::", "security::"]
    }
    prefixes = relevant_prefixes.get(domain, relevant_prefixes["general"])
    sample = []
    for prefix in prefixes:
        keys = [k for k in ICON_KEYS if k.startswith(prefix)][:8]
        sample.extend(keys)
    return "\n".join(sample[:60])

def generate_diagram(prompt: str, domain: str, classified: dict, rag_context: str) -> dict:
    domain_rules = DOMAIN_RULES.get(domain, DOMAIN_RULES["general"])
    icon_sample = get_icon_sample(domain)

    system = SYSTEM_PROMPT.format(
        icon_count=len(ICON_KEYS),
        icon_sample=icon_sample
    )

    user_message = f"""Generate an architecture diagram for:
{prompt}

DOMAIN: {domain.upper()}
CLOUD: {classified.get('cloud', 'aws')}
COMPLIANCE: {', '.join(classified.get('compliance', []))}

DOMAIN RULES TO FOLLOW:
{domain_rules}

REFERENCE CONTEXT FROM STANDARDS DOCUMENTS:
{rag_context}

Generate a complete, detailed architecture diagram JSON following the rules above.
Use specific product names. Include all necessary components for a production system.
Every node must have a real icon key from the list provided."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_message}
        ],
        max_tokens=3000,
        temperature=0.3
    )

    raw = response.choices[0].message.content
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        diagram = json.loads(raw)
        return {"status": "success", "diagram": diagram}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": str(e), "raw": raw}