import re
path = "/Users/SatvikMishra/Desktop/basaltcode/backend/diagram_generator.py"
with open(path) as f:
    content = f.read()

flow_rules = """

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
"""

# 1. Add flow rules to the OT block (before its closing triple-quote)
m = re.search(r'(    "ot": """)(.*?)(""",\n)', content, flags=re.DOTALL)
if not m:
    print("ERROR: OT rule not found"); exit()
ot_body_with_flow = m.group(2) + flow_rules
content = content[:m.start(2)] + ot_body_with_flow + content[m.end(2):]
print("flow rules added to OT")

# 2. Copy the updated OT body into metal/fmcg/scada
m2 = re.search(r'    "ot": """(.*?)""",\n', content, flags=re.DOTALL)
ot_body = m2.group(1)
for domain in ["fmcg", "metal", "scada"]:
    pattern = r'    "' + domain + r'": """.*?""",\n'
    repl = '    "' + domain + '": """' + ot_body + '""",\n'
    new_content = re.sub(pattern, repl, content, count=1, flags=re.DOTALL)
    if new_content != content:
        content = new_content
        print(f"{domain} synced with new OT rules")
    else:
        print(f"WARNING: {domain} not synced")

with open(path, "w") as f:
    f.write(content)
print("DONE")