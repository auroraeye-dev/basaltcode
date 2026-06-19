# Appends structural rules to validator.py: L3->L2 firewall, OT AD, SIEM forwarding, Safety system
path = "/Users/SatvikMishra/Desktop/basaltcode/backend/validator.py"
with open(path) as f:
    content = f.read()

new_rules = '''

def ensure_l3_l2_firewall(diagram, domain):
    """Insert an Industrial Firewall between Level 3 and the cells, and route
    SCADA/Level 3 -> Industrial Firewall -> cell PLCs (IEC 62443 boundary)."""
    if not diagram.get("cells"):
        return diagram
    nodes = diagram.get("nodes", [])
    # already has an industrial firewall near level_3? (not the IDMZ ones)
    has_ind_fw = any(classify(n) == "firewall" and _node_zone(n) == "level_3" for n in nodes)
    fw_id = "v_l3l2_firewall"
    if not has_ind_fw:
        diagram["nodes"].append({
            "id": fw_id, "label": "Industrial Firewall (L3/L2)", "icon": "security::Fortinet",
            "zone": "level_3",
            "description": "Security boundary between Site Operations (L3) and control cells (L2) per IEC 62443 (added by validator)."
        })
        for z in diagram.get("zones", []):
            if z.get("id") == "level_3":
                z.setdefault("nodes", []).append(fw_id)
    else:
        fw_id = next(n["id"] for n in nodes if classify(n) == "firewall" and _node_zone(n) == "level_3")

    # Route SCADA -> firewall -> each cell PLC (replace direct SCADA->PLC)
    byid = {n["id"]: n for n in diagram["nodes"]}
    scada = next((n["id"] for n in diagram["nodes"] if classify(n) == "scada" and "historian" not in _node_label(n)), None)
    if scada:
        _add_edge(diagram, scada, fw_id, "OPC-UA :4840")
    for cell in diagram.get("cells", []):
        for nid in cell.get("nodes") or []:
            if nid in byid and classify(byid[nid]) == "plc":
                # remove direct scada->plc, route through firewall
                if scada:
                    _remove_edge(diagram, scada, nid)
                _add_edge(diagram, fw_id, nid, "OPC-UA :4840")
    return diagram

def ensure_ot_ad(diagram, domain):
    """Add an OT Active Directory in Level 3 and connect key OT assets to it."""
    nodes = diagram.get("nodes", [])
    has_ot_ad = any(classify(n) == "ad" and _node_zone(n) in ("level_3", "dmz") for n in nodes)
    if has_ot_ad:
        return diagram
    ad_id = "v_ot_ad"
    diagram["nodes"].append({
        "id": ad_id, "label": "OT Active Directory", "icon": "generic::Active Directory",
        "zone": "level_3",
        "description": "Dedicated OT domain controller; OT assets authenticate here, separate from Enterprise AD (added by validator)."
    })
    for z in diagram.get("zones", []):
        if z.get("id") == "level_3":
            z.setdefault("nodes", []).append(ad_id)
    # connect engineering WS, SCADA, historian to OT AD
    for n in diagram["nodes"]:
        if classify(n) in ("scada", "historian") or _is(n, "engineering", "workstation"):
            if _node_zone(n) == "level_3" and n["id"] != ad_id:
                _add_edge(diagram, n["id"], ad_id, "Auth", "dashed")
    return diagram

def ensure_siem_forwarding(diagram):
    """OT SOC -> Enterprise SIEM, Firewalls -> SIEM, Jump Server -> SIEM."""
    nodes = diagram.get("nodes", [])
    siem = next((n for n in nodes if classify(n) == "siem"), None)
    if not siem:
        return diagram
    for n in nodes:
        c = classify(n)
        if c in ("monitoring", "firewall") and n["id"] != siem["id"]:
            _add_edge(diagram, n["id"], siem["id"], "Log Forward", "dashed")
        if _is(n, "jump", "bastion"):
            _add_edge(diagram, n["id"], siem["id"], "Log Forward", "dashed")
    return diagram

def ensure_safety_system(diagram, domain):
    """For power/process plants, ensure a Safety Instrumented System exists at level_3 or in a cell."""
    has_safety = any(classify(n) == "safety" for n in diagram.get("nodes", []))
    if has_safety:
        return diagram
    sid = "v_sis"
    diagram["nodes"].append({
        "id": sid, "label": "Safety Instrumented System (SIS)", "icon": "plc::Safety",
        "zone": "level_3",
        "description": "Independent safety/ESD system, separated from normal control per IEC 61511 (added by validator)."
    })
    for z in diagram.get("zones", []):
        if z.get("id") == "level_3":
            z.setdefault("nodes", []).append(sid)
    return diagram
'''

# insert the new functions before main_validate
marker = "def main_validate("
content = content.replace(marker, new_rules + "\n" + marker, 1)

# extend main_validate to call them
old_body = '''    if industrial:
        diagram = ensure_scada_master(diagram, domain)
        diagram = fix_field_flow(diagram)
        diagram = fix_historian_replication(diagram)
        diagram = fix_monitoring_feeds(diagram)
    return diagram'''
new_body = '''    if industrial:
        diagram = ensure_scada_master(diagram, domain)
        diagram = fix_field_flow(diagram)
        diagram = ensure_l3_l2_firewall(diagram, domain)
        diagram = ensure_ot_ad(diagram, domain)
        diagram = fix_historian_replication(diagram)
        diagram = fix_monitoring_feeds(diagram)
        diagram = ensure_siem_forwarding(diagram)
        if domain in ("ot", "metal", "scada"):
            diagram = ensure_safety_system(diagram, domain)
    return diagram'''
content = content.replace(old_body, new_body)

with open(path, "w") as f:
    f.write(content)

import ast
ast.parse(content)
print("validator v2 written and syntax OK")