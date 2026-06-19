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
CPwE / PURDUE MODEL — full reference structure. Build ALL these levels top to bottom:

ZONE ORDER (each is a zone; use these exact ids and types):
1. zone id "level_5", type "enterprise", label "Level 5 — Enterprise Network (Zone: Enterprise)"
   Components: ERP/SAP (sap::Erp), Corp Email (generic::Email), Active Directory (generic::Active Directory), Enterprise SIEM (security::Splunk), Internet (generic::Internet), Perimeter Firewall (security::Palo Alto)
2. zone id "level_4", type "enterprise", label "Level 4 — Site Business Planning & Logistics"
   Components: Production Scheduling (generic::Server), QMS/PLM (sap::Erp), Inventory/WMS (generic::Database)
3. zone id "dmz", type "dmz", label "Industrial DMZ (IDMZ) — Conduit between Enterprise & Industrial"
   MUST contain: Enterprise-facing Firewall (security::Palo Alto), Industrial-facing Firewall (security::Fortinet), Patch/WSUS (generic::Server), AV/Defender (security::Sophos), Remote Access Jump (generic::Jump Server), Data Broker/Historian Mirror (scada::Osisoft Pi), Reverse Proxy (generic::Server)
4. zone id "level_3", type "onprem", label "Level 3 — Site Operations (Industrial Zone)"
   Components: MES (scada::Ignition), Plant Historian (scada::Osisoft Pi), Engineering Workstation (generic::Server), Asset Inventory / OT Monitoring (security::Claroty), OT SOC/IDS (security::Dragos), Core Switch Stack (cisco::Switch or hardware::Switch)
5. Levels 2/1/0 -> SPLIT INTO CELLS (see Cell/Area Zones rules)

MANDATORY:
- ALWAYS include Level 5 AND Level 4 as SEPARATE zones — never merge them.
- ALWAYS include Internet + Perimeter Firewall in Level 5 (the outside-world boundary).
- The IDMZ has the TWO-firewall sandwich (Palo Alto enterprise-facing + Fortinet industrial-facing).
- Enterprise (5) -> Level 4 -> IDMZ -> Level 3 -> Cells. NEVER skip the IDMZ.
- Edge labels between zones use conduit terms: "Conduit (FW)", "Enterprise to Site Business", "OPC-UA :4840", "EtherNet/IP :44818".
- Use OPC-UA :4840 from Level 3 down to cells; EtherNet/IP or PROFINET inside cells.
- NEVER create a "Purdue Model Reference" node or any pattern/reference node.


EDGE & DATA-FLOW RULES (CRITICAL — get the direction right):
- FIELD FLOW: Sensors send data UP to the PLC. Edges go Sensors -> PLC (label "Sensor Data"), and PLC -> Actuators (label "Control Signal"). NEVER draw PLC -> Sensors as the primary data path.
- CELL HIERARCHY: PLC <-> HMI (label "Monitoring / Control"). The HMI does NOT sit between PLC and field devices. Vertical order in a cell top to bottom: HMI (L2), PLC (L1), Sensors+Actuators (L0). Data flows Sensors -> PLC -> HMI; commands flow HMI -> PLC -> Actuators.
- SCADA MASTER: Always include a SCADA Server (scada::Ignition or scada::Wonderware) at Level 2 or 3 that POLLS the PLCs. Edge: SCADA Server -> each cell PLC (label "OPC-UA :4840"). MES and Historian are NOT the SCADA master.
- OPC-UA TERMINATION: OPC-UA conduits terminate on PLCs, SCADA Servers, or Historians — NEVER on an HMI. Level 3 -> cell connections go to the cell PLC or SCADA, not the HMI.
- IDMZ ROUTING (no bypass): Enterprise (L5) and L4 traffic must enter the Enterprise-facing Firewall, cross the IDMZ, exit the Industrial-facing Firewall, then reach Level 3. NEVER connect an enterprise/L4 node directly to a Level 3 node. NEVER terminate an L4 node on the perimeter firewall as an endpoint.
- HISTORIAN REPLICATION: Plant Historian (L3) -> Historian Mirror (IDMZ) labeled "Replication"; Historian Mirror -> enterprise consumer labeled "Read-only". Must not float.
- REVERSE PROXY: connect what it fronts (Historian web / MES dashboards) -> Reverse Proxy -> enterprise users. Never dangling.
- OT MONITORING: OT SOC/IDS and Asset Inventory (Claroty/Dragos) get edges from the Core Switch Stack labeled "SPAN / Mirror" so it is clear what they monitor.
- LABEL EVERY EDGE: OPC-UA :4840, EtherNet/IP :44818, Modbus/TCP, HTTPS, Replication, Sensor Data, Control Signal, SPAN.
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
CPwE / PURDUE MODEL — full reference structure. Build ALL these levels top to bottom:

ZONE ORDER (each is a zone; use these exact ids and types):
1. zone id "level_5", type "enterprise", label "Level 5 — Enterprise Network (Zone: Enterprise)"
   Components: ERP/SAP (sap::Erp), Corp Email (generic::Email), Active Directory (generic::Active Directory), Enterprise SIEM (security::Splunk), Internet (generic::Internet), Perimeter Firewall (security::Palo Alto)
2. zone id "level_4", type "enterprise", label "Level 4 — Site Business Planning & Logistics"
   Components: Production Scheduling (generic::Server), QMS/PLM (sap::Erp), Inventory/WMS (generic::Database)
3. zone id "dmz", type "dmz", label "Industrial DMZ (IDMZ) — Conduit between Enterprise & Industrial"
   MUST contain: Enterprise-facing Firewall (security::Palo Alto), Industrial-facing Firewall (security::Fortinet), Patch/WSUS (generic::Server), AV/Defender (security::Sophos), Remote Access Jump (generic::Jump Server), Data Broker/Historian Mirror (scada::Osisoft Pi), Reverse Proxy (generic::Server)
4. zone id "level_3", type "onprem", label "Level 3 — Site Operations (Industrial Zone)"
   Components: MES (scada::Ignition), Plant Historian (scada::Osisoft Pi), Engineering Workstation (generic::Server), Asset Inventory / OT Monitoring (security::Claroty), OT SOC/IDS (security::Dragos), Core Switch Stack (cisco::Switch or hardware::Switch)
5. Levels 2/1/0 -> SPLIT INTO CELLS (see Cell/Area Zones rules)

MANDATORY:
- ALWAYS include Level 5 AND Level 4 as SEPARATE zones — never merge them.
- ALWAYS include Internet + Perimeter Firewall in Level 5 (the outside-world boundary).
- The IDMZ has the TWO-firewall sandwich (Palo Alto enterprise-facing + Fortinet industrial-facing).
- Enterprise (5) -> Level 4 -> IDMZ -> Level 3 -> Cells. NEVER skip the IDMZ.
- Edge labels between zones use conduit terms: "Conduit (FW)", "Enterprise to Site Business", "OPC-UA :4840", "EtherNet/IP :44818".
- Use OPC-UA :4840 from Level 3 down to cells; EtherNet/IP or PROFINET inside cells.
- NEVER create a "Purdue Model Reference" node or any pattern/reference node.


EDGE & DATA-FLOW RULES (CRITICAL — get the direction right):
- FIELD FLOW: Sensors send data UP to the PLC. Edges go Sensors -> PLC (label "Sensor Data"), and PLC -> Actuators (label "Control Signal"). NEVER draw PLC -> Sensors as the primary data path.
- CELL HIERARCHY: PLC <-> HMI (label "Monitoring / Control"). The HMI does NOT sit between PLC and field devices. Vertical order in a cell top to bottom: HMI (L2), PLC (L1), Sensors+Actuators (L0). Data flows Sensors -> PLC -> HMI; commands flow HMI -> PLC -> Actuators.
- SCADA MASTER: Always include a SCADA Server (scada::Ignition or scada::Wonderware) at Level 2 or 3 that POLLS the PLCs. Edge: SCADA Server -> each cell PLC (label "OPC-UA :4840"). MES and Historian are NOT the SCADA master.
- OPC-UA TERMINATION: OPC-UA conduits terminate on PLCs, SCADA Servers, or Historians — NEVER on an HMI. Level 3 -> cell connections go to the cell PLC or SCADA, not the HMI.
- IDMZ ROUTING (no bypass): Enterprise (L5) and L4 traffic must enter the Enterprise-facing Firewall, cross the IDMZ, exit the Industrial-facing Firewall, then reach Level 3. NEVER connect an enterprise/L4 node directly to a Level 3 node. NEVER terminate an L4 node on the perimeter firewall as an endpoint.
- HISTORIAN REPLICATION: Plant Historian (L3) -> Historian Mirror (IDMZ) labeled "Replication"; Historian Mirror -> enterprise consumer labeled "Read-only". Must not float.
- REVERSE PROXY: connect what it fronts (Historian web / MES dashboards) -> Reverse Proxy -> enterprise users. Never dangling.
- OT MONITORING: OT SOC/IDS and Asset Inventory (Claroty/Dragos) get edges from the Core Switch Stack labeled "SPAN / Mirror" so it is clear what they monitor.
- LABEL EVERY EDGE: OPC-UA :4840, EtherNet/IP :44818, Modbus/TCP, HTTPS, Replication, Sensor Data, Control Signal, SPAN.
""",
    "metal": """
CPwE / PURDUE MODEL — full reference structure. Build ALL these levels top to bottom:

ZONE ORDER (each is a zone; use these exact ids and types):
1. zone id "level_5", type "enterprise", label "Level 5 — Enterprise Network (Zone: Enterprise)"
   Components: ERP/SAP (sap::Erp), Corp Email (generic::Email), Active Directory (generic::Active Directory), Enterprise SIEM (security::Splunk), Internet (generic::Internet), Perimeter Firewall (security::Palo Alto)
2. zone id "level_4", type "enterprise", label "Level 4 — Site Business Planning & Logistics"
   Components: Production Scheduling (generic::Server), QMS/PLM (sap::Erp), Inventory/WMS (generic::Database)
3. zone id "dmz", type "dmz", label "Industrial DMZ (IDMZ) — Conduit between Enterprise & Industrial"
   MUST contain: Enterprise-facing Firewall (security::Palo Alto), Industrial-facing Firewall (security::Fortinet), Patch/WSUS (generic::Server), AV/Defender (security::Sophos), Remote Access Jump (generic::Jump Server), Data Broker/Historian Mirror (scada::Osisoft Pi), Reverse Proxy (generic::Server)
4. zone id "level_3", type "onprem", label "Level 3 — Site Operations (Industrial Zone)"
   Components: MES (scada::Ignition), Plant Historian (scada::Osisoft Pi), Engineering Workstation (generic::Server), Asset Inventory / OT Monitoring (security::Claroty), OT SOC/IDS (security::Dragos), Core Switch Stack (cisco::Switch or hardware::Switch)
5. Levels 2/1/0 -> SPLIT INTO CELLS (see Cell/Area Zones rules)

MANDATORY:
- ALWAYS include Level 5 AND Level 4 as SEPARATE zones — never merge them.
- ALWAYS include Internet + Perimeter Firewall in Level 5 (the outside-world boundary).
- The IDMZ has the TWO-firewall sandwich (Palo Alto enterprise-facing + Fortinet industrial-facing).
- Enterprise (5) -> Level 4 -> IDMZ -> Level 3 -> Cells. NEVER skip the IDMZ.
- Edge labels between zones use conduit terms: "Conduit (FW)", "Enterprise to Site Business", "OPC-UA :4840", "EtherNet/IP :44818".
- Use OPC-UA :4840 from Level 3 down to cells; EtherNet/IP or PROFINET inside cells.
- NEVER create a "Purdue Model Reference" node or any pattern/reference node.


EDGE & DATA-FLOW RULES (CRITICAL — get the direction right):
- FIELD FLOW: Sensors send data UP to the PLC. Edges go Sensors -> PLC (label "Sensor Data"), and PLC -> Actuators (label "Control Signal"). NEVER draw PLC -> Sensors as the primary data path.
- CELL HIERARCHY: PLC <-> HMI (label "Monitoring / Control"). The HMI does NOT sit between PLC and field devices. Vertical order in a cell top to bottom: HMI (L2), PLC (L1), Sensors+Actuators (L0). Data flows Sensors -> PLC -> HMI; commands flow HMI -> PLC -> Actuators.
- SCADA MASTER: Always include a SCADA Server (scada::Ignition or scada::Wonderware) at Level 2 or 3 that POLLS the PLCs. Edge: SCADA Server -> each cell PLC (label "OPC-UA :4840"). MES and Historian are NOT the SCADA master.
- OPC-UA TERMINATION: OPC-UA conduits terminate on PLCs, SCADA Servers, or Historians — NEVER on an HMI. Level 3 -> cell connections go to the cell PLC or SCADA, not the HMI.
- IDMZ ROUTING (no bypass): Enterprise (L5) and L4 traffic must enter the Enterprise-facing Firewall, cross the IDMZ, exit the Industrial-facing Firewall, then reach Level 3. NEVER connect an enterprise/L4 node directly to a Level 3 node. NEVER terminate an L4 node on the perimeter firewall as an endpoint.
- HISTORIAN REPLICATION: Plant Historian (L3) -> Historian Mirror (IDMZ) labeled "Replication"; Historian Mirror -> enterprise consumer labeled "Read-only". Must not float.
- REVERSE PROXY: connect what it fronts (Historian web / MES dashboards) -> Reverse Proxy -> enterprise users. Never dangling.
- OT MONITORING: OT SOC/IDS and Asset Inventory (Claroty/Dragos) get edges from the Core Switch Stack labeled "SPAN / Mirror" so it is clear what they monitor.
- LABEL EVERY EDGE: OPC-UA :4840, EtherNet/IP :44818, Modbus/TCP, HTTPS, Replication, Sensor Data, Control Signal, SPAN.
""",
    "scada": """
CPwE / PURDUE MODEL — full reference structure. Build ALL these levels top to bottom:

ZONE ORDER (each is a zone; use these exact ids and types):
1. zone id "level_5", type "enterprise", label "Level 5 — Enterprise Network (Zone: Enterprise)"
   Components: ERP/SAP (sap::Erp), Corp Email (generic::Email), Active Directory (generic::Active Directory), Enterprise SIEM (security::Splunk), Internet (generic::Internet), Perimeter Firewall (security::Palo Alto)
2. zone id "level_4", type "enterprise", label "Level 4 — Site Business Planning & Logistics"
   Components: Production Scheduling (generic::Server), QMS/PLM (sap::Erp), Inventory/WMS (generic::Database)
3. zone id "dmz", type "dmz", label "Industrial DMZ (IDMZ) — Conduit between Enterprise & Industrial"
   MUST contain: Enterprise-facing Firewall (security::Palo Alto), Industrial-facing Firewall (security::Fortinet), Patch/WSUS (generic::Server), AV/Defender (security::Sophos), Remote Access Jump (generic::Jump Server), Data Broker/Historian Mirror (scada::Osisoft Pi), Reverse Proxy (generic::Server)
4. zone id "level_3", type "onprem", label "Level 3 — Site Operations (Industrial Zone)"
   Components: MES (scada::Ignition), Plant Historian (scada::Osisoft Pi), Engineering Workstation (generic::Server), Asset Inventory / OT Monitoring (security::Claroty), OT SOC/IDS (security::Dragos), Core Switch Stack (cisco::Switch or hardware::Switch)
5. Levels 2/1/0 -> SPLIT INTO CELLS (see Cell/Area Zones rules)

MANDATORY:
- ALWAYS include Level 5 AND Level 4 as SEPARATE zones — never merge them.
- ALWAYS include Internet + Perimeter Firewall in Level 5 (the outside-world boundary).
- The IDMZ has the TWO-firewall sandwich (Palo Alto enterprise-facing + Fortinet industrial-facing).
- Enterprise (5) -> Level 4 -> IDMZ -> Level 3 -> Cells. NEVER skip the IDMZ.
- Edge labels between zones use conduit terms: "Conduit (FW)", "Enterprise to Site Business", "OPC-UA :4840", "EtherNet/IP :44818".
- Use OPC-UA :4840 from Level 3 down to cells; EtherNet/IP or PROFINET inside cells.
- NEVER create a "Purdue Model Reference" node or any pattern/reference node.


EDGE & DATA-FLOW RULES (CRITICAL — get the direction right):
- FIELD FLOW: Sensors send data UP to the PLC. Edges go Sensors -> PLC (label "Sensor Data"), and PLC -> Actuators (label "Control Signal"). NEVER draw PLC -> Sensors as the primary data path.
- CELL HIERARCHY: PLC <-> HMI (label "Monitoring / Control"). The HMI does NOT sit between PLC and field devices. Vertical order in a cell top to bottom: HMI (L2), PLC (L1), Sensors+Actuators (L0). Data flows Sensors -> PLC -> HMI; commands flow HMI -> PLC -> Actuators.
- SCADA MASTER: Always include a SCADA Server (scada::Ignition or scada::Wonderware) at Level 2 or 3 that POLLS the PLCs. Edge: SCADA Server -> each cell PLC (label "OPC-UA :4840"). MES and Historian are NOT the SCADA master.
- OPC-UA TERMINATION: OPC-UA conduits terminate on PLCs, SCADA Servers, or Historians — NEVER on an HMI. Level 3 -> cell connections go to the cell PLC or SCADA, not the HMI.
- IDMZ ROUTING (no bypass): Enterprise (L5) and L4 traffic must enter the Enterprise-facing Firewall, cross the IDMZ, exit the Industrial-facing Firewall, then reach Level 3. NEVER connect an enterprise/L4 node directly to a Level 3 node. NEVER terminate an L4 node on the perimeter firewall as an endpoint.
- HISTORIAN REPLICATION: Plant Historian (L3) -> Historian Mirror (IDMZ) labeled "Replication"; Historian Mirror -> enterprise consumer labeled "Read-only". Must not float.
- REVERSE PROXY: connect what it fronts (Historian web / MES dashboards) -> Reverse Proxy -> enterprise users. Never dangling.
- OT MONITORING: OT SOC/IDS and Asset Inventory (Claroty/Dragos) get edges from the Core Switch Stack labeled "SPAN / Mirror" so it is clear what they monitor.
- LABEL EVERY EDGE: OPC-UA :4840, EtherNet/IP :44818, Modbus/TCP, HTTPS, Replication, Sensor Data, Control Signal, SPAN.
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
  ],
  "cells": [
    {{
      "id": "cell_id",
      "label": "Production Cell Name (e.g. Body Shop, Paint Shop, Packaging Line)",
      "nodes": ["node_id_list — the L2/L1/L0 nodes belonging to THIS cell"]
    }}
  ]
}}

CELL/AREA ZONES (IMPORTANT):
- When a facility naturally has multiple parallel production areas (automotive: Body Shop / Paint Shop / Final Assembly; FMCG: Mixing / Filling / Packaging; metal: Furnace / Casting / Rolling), split Levels 2/1/0 into CELLS.
- Each cell is a vertical mini-stack: its own HMI/SCADA (L2), its own PLC (L1), its own field devices (L0).
- CRITICAL: when you use cells, EVERY node at level_2, level_1, and level_0 MUST be assigned to exactly one cell. Leave NONE unassigned.
- BALANCE RULE: every cell MUST have the SAME complete vertical stack — do NOT dump most nodes into one cell. Each cell gets: its own HMI or local SCADA (level_2), its own PLC (level_1), its own sensors AND actuators (level_0). If you create 3 cells, you create roughly 3x4 = 12 lower-level nodes, 4 per cell.
- Do NOT leave any cell with fewer nodes than the others. Body Shop, Paint Shop, and Assembly must each be a full stack.
- Plant-wide shared systems (one site-wide SCADA, one Area Historian) belong at level_3, NOT inside a single cell and NOT dangling at level_2.
- Each cell should contain its OWN L2 HMI/SCADA, its OWN L1 PLC, and its OWN L0 field devices. Give each cell a full vertical stack.
- Example per cell: Body Shop = [L2: HMI, L1: ControlLogix PLC, L0: Weld Robots + Sensors]; Paint Shop = [L2: HMI, L1: PLC, L0: Paint Robots + Booth]; Assembly = [L2: HMI, L1: PLC, L0: Conveyor + Torque Tools].
- Put each lower-level node in BOTH its zone (level_2/level_1/level_0) AND its cell (via the cells array). Every level_2/1/0 node id must appear in some cell's nodes list.
- Shared supervisory systems (Area Historian, plant-wide SCADA) can stay at level_3 instead — do NOT leave them dangling at level_2 outside a cell.
- Use job-specific equipment per cell: weld robots in body shop, paint robots in paint shop, conveyors in assembly.
- If the system has only ONE production area or is a simple network, leave "cells" as an empty array [].
- Upper levels (Enterprise, DMZ, Level 3) are NEVER split into cells — they stay shared."""

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
        max_tokens=8000,
        temperature=0.3
    )

    raw = response.choices[0].message.content
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        diagram = json.loads(raw)
        return {"status": "success", "diagram": diagram}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": str(e), "raw": raw}