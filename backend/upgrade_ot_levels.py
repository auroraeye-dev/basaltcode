import re
path = "/Users/SatvikMishra/Desktop/basaltcode/backend/diagram_generator.py"
with open(path) as f:
    content = f.read()

new_ot = '''    "ot": """
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
""",'''

pattern = r'    "ot": """.*?""",\n(?=    "pharma":)'
new_content = re.sub(pattern, new_ot + "\n", content, count=1, flags=re.DOTALL)

if new_content == content:
    print("WARNING: OT block not found / not replaced")
else:
    with open(path, "w") as f:
        f.write(new_content)
    print("OT rules upgraded with Level 5/4 split, Internet, richer Level 3")