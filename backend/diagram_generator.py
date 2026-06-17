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
CPwE / PURDUE MODEL STRUCTURE — follow this EXACTLY top to bottom:

ZONE ORDER (top to bottom):
1. Enterprise Zone (zone id "level_4") — ERP, Email, Active Directory, Enterprise users, Internet access
2. Industrial DMZ (zone id "dmz") — sits BETWEEN enterprise and industrial. MUST contain: Enterprise-facing Firewall (security::Palo Alto), Industrial-facing Firewall (security::Fortinet), OPC-UA Gateway, Jump Server
3. Level 3 Site Operations (zone id "level_3") — MES, Site Historian, Application Servers, OT monitoring (security::Claroty or security::Dragos)
4. Level 2 Supervisory (zone id "level_2") — SCADA, HMI, Area Historian
5. Level 1 Machine Control (zone id "level_1") — PLCs, Safety PLC
6. Level 0 Field (zone id "level_0") — Sensors, Actuators, Drives

MANDATORY RULES:
- ALWAYS include the Enterprise Zone (level_4) at the TOP — never omit it
- The IDMZ MUST have TWO firewalls: security::Palo Alto facing enterprise, security::Fortinet facing industrial (CPwE two-firewall sandwich)
- Enterprise (level_4) connects DOWN to the IDMZ; IDMZ connects DOWN to Level 3
- NEVER connect Enterprise directly to Level 3 — all traffic crosses the IDMZ
- Use OPC-UA :4840 between Level 3 and Level 2
- Use EtherNet/IP :44818 or PROFINET between Level 1 and Level 0
- DO NOT create a "Purdue Model Reference" node — it is NOT a component
- DO NOT add any pattern or reference nodes — only real architectural components
- Every zone must have a "type": level_4 -> enterprise, dmz -> dmz, level_3/2/1/0 -> onprem

ICONS:
- industrial::Opcua Gateway, generic::Jump Server
- security::Palo Alto, security::Fortinet, security::Claroty, security::Dragos
- plc::Allen Bradley, plc::Siemens S7
- scada::Ignition, scada::Wonderware, scada::Osisoft Pi, scada::Hmi
- industrial::Sensor, industrial::Actuator
- sap::Erp, generic::Users for enterprise
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

    user_message = f"""REFERENCE CONTEXT — real architecture knowledge extracted from authoritative standards documents and their diagrams. Build the architecture from THIS:
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
Output ONLY the JSON."""

    response = client.chat.completions.create(
        model="gpt-4o",
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