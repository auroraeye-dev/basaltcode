"""
Basalt deterministic architecture validator.
Runs AFTER the LLM generates a diagram and enforces engineering-correct
structure and data-flow rules that the LLM cannot be trusted to get right.

Each rule is deterministic, so output is 100% consistent.
This is Basalt's compliance/consistency engine (Stage 2 moat).
"""

# --- helpers -------------------------------------------------------------

def _node_label(node):
    return (node.get("label") or "").lower()

def _node_zone(node):
    return node.get("zone") or ""

def _find_nodes(diagram, predicate):
    return [n for n in diagram.get("nodes", []) if predicate(n)]

def _node_in_cell(diagram, node_id):
    for c in diagram.get("cells", []):
        if node_id in (c.get("nodes") or []):
            return c
    return None

def _cell_of(diagram, node_id):
    c = _node_in_cell(diagram, node_id)
    return c.get("id") if c else None

def _edge_exists(diagram, frm, to):
    for e in diagram.get("edges", []):
        if e.get("from") == frm and e.get("to") == to:
            return True
    return False

def _add_edge(diagram, frm, to, label, style="solid"):
    if frm == to or _edge_exists(diagram, frm, to):
        return
    diagram.setdefault("edges", []).append({
        "id": f"v_{frm}_{to}",
        "from": frm, "to": to, "label": label, "style": style,
    })

def _remove_edge(diagram, frm, to):
    diagram["edges"] = [e for e in diagram.get("edges", [])
                        if not (e.get("from") == frm and e.get("to") == to)]

# --- node type classification (by label keywords) ------------------------

def _is(node, *keywords):
    lbl = _node_label(node)
    return any(k in lbl for k in keywords)

def classify(node):
    if _is(node, "sensor"): return "sensor"
    if _is(node, "actuator"): return "actuator"
    if _is(node, "vfd", "variable frequency", "drive"): return "vfd"
    if _is(node, "safety relay", "safety plc", "safety"): return "safety"
    if _is(node, "plc", "controllogix", "compactlogix", "siemens s7", "rtu", "ied", "controller"): return "plc"
    if _is(node, "hmi"): return "hmi"
    if _is(node, "scada"): return "scada"
    if _is(node, "historian"): return "historian"
    if _is(node, "mes"): return "mes"
    if _is(node, "firewall"): return "firewall"
    if _is(node, "switch", "core switch"): return "switch"
    if _is(node, "soc", "ids", "claroty", "dragos", "nozomi"): return "monitoring"
    if _is(node, "siem", "splunk"): return "siem"
    if _is(node, "active directory", "domain controller"): return "ad"
    return "other"

# --- RULE PASSES ---------------------------------------------------------

def fix_field_flow(diagram):
    """Sensors -> PLC -> Actuators/VFD. PLC <-> HMI. Safety -> PLC.
    Flip or reroute any backwards edges among cell devices."""
    nodes = diagram.get("nodes", [])
    byid = {n["id"]: n for n in nodes}

    # group cell devices per cell
    for cell in diagram.get("cells", []):
        ids = cell.get("nodes") or []
        types = {nid: classify(byid[nid]) for nid in ids if nid in byid}
        plc = next((nid for nid, t in types.items() if t == "plc"), None)
        hmi = next((nid for nid, t in types.items() if t == "hmi"), None)
        scada = next((nid for nid, t in types.items() if t == "scada"), None)
        sensors = [nid for nid, t in types.items() if t == "sensor"]
        actuators = [nid for nid, t in types.items() if t in ("actuator", "vfd")]
        safeties = [nid for nid, t in types.items() if t == "safety"]

        controller = plc or scada
        if not controller:
            continue

        # Remove any wrong edges between these devices, then re-add correct ones
        cell_ids = set(ids)
        diagram["edges"] = [
            e for e in diagram.get("edges", [])
            if not (e.get("from") in cell_ids and e.get("to") in cell_ids)
        ]

        # Sensors -> PLC
        for s in sensors:
            _add_edge(diagram, s, controller, "Sensor Data")
        # PLC -> Actuators / VFD
        for a in actuators:
            _add_edge(diagram, controller, a, "Control Signal")
        # Safety -> PLC (safety feeds/intervenes the controller)
        for sf in safeties:
            _add_edge(diagram, sf, controller, "Safety Interlock")
        # PLC <-> HMI
        if hmi:
            _add_edge(diagram, controller, hmi, "Monitoring")
        # SCADA polls PLC if both present
        if scada and plc and scada != plc:
            _add_edge(diagram, scada, plc, "OPC-UA :4840")

    return diagram

def ensure_scada_master(diagram, domain):
    """If cells exist but no SCADA server polls PLCs, add one at Level 3."""
    if not diagram.get("cells"):
        return diagram
    has_scada = any(classify(n) == "scada" and "historian" not in _node_label(n)
                    for n in diagram.get("nodes", []))
    if has_scada:
        return diagram
    # add a SCADA master at level_3
    sid = "v_scada_master"
    diagram["nodes"].append({
        "id": sid, "label": "SCADA Server", "icon": "scada::Ignition",
        "zone": "level_3", "description": "Supervisory control server polling cell PLCs (added by validator)."
    })
    # add to level_3 zone node list if present
    for z in diagram.get("zones", []):
        if z.get("id") == "level_3":
            z.setdefault("nodes", []).append(sid)
    # connect SCADA -> each cell PLC
    byid = {n["id"]: n for n in diagram["nodes"]}
    for cell in diagram.get("cells", []):
        for nid in cell.get("nodes") or []:
            if nid in byid and classify(byid[nid]) == "plc":
                _add_edge(diagram, sid, nid, "OPC-UA :4840")
    return diagram

def fix_historian_replication(diagram):
    """Plant Historian (L3) -> Historian Mirror (IDMZ) labeled Replication."""
    nodes = diagram.get("nodes", [])
    plant_hist = next((n for n in nodes if classify(n) == "historian"
                       and _node_zone(n) in ("level_3",) and "mirror" not in _node_label(n)), None)
    mirror = next((n for n in nodes if "mirror" in _node_label(n)
                   or (classify(n) == "historian" and _node_zone(n) == "dmz")), None)
    if plant_hist and mirror and plant_hist["id"] != mirror["id"]:
        _add_edge(diagram, plant_hist["id"], mirror["id"], "Replication", "dashed")
    return diagram

def fix_monitoring_feeds(diagram):
    """OT SOC/IDS <- Core Switch (SPAN). Firewalls -> SIEM (logs)."""
    nodes = diagram.get("nodes", [])
    switch = next((n for n in nodes if classify(n) == "switch"), None)
    monitors = [n for n in nodes if classify(n) == "monitoring"]
    siem = next((n for n in nodes if classify(n) == "siem"), None)
    firewalls = [n for n in nodes if classify(n) == "firewall"]

    if switch:
        for m in monitors:
            _add_edge(diagram, switch["id"], m["id"], "SPAN / Mirror", "dashed")
    if siem:
        for m in monitors:
            _add_edge(diagram, m["id"], siem["id"], "Log Forward", "dashed")
        for f in firewalls:
            _add_edge(diagram, f["id"], siem["id"], "Log Forward", "dashed")
    return diagram



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



# --- ICON CORRECTION ---------------------------------------------------
# Map recognizable service/product names to their CORRECT icon key.
# Overrides the LLM when it picks the wrong namespace (e.g. CloudWatch -> azure).
# Match is case-insensitive substring on the node label; first match wins.
ICON_NAME_MAP = [
    # AWS services
    ("cloudwatch", "aws::Amazon CloudWatch"),
    ("aws waf", "aws::AWS WAF"),
    ("web application firewall", "aws::AWS WAF"),
    ("elastic load", "aws::Elastic Load Balancing"),
    ("load balancer", "aws::Elastic Load Balancing"),
    ("application load balancer", "aws::Elastic Load Balancing"),
    ("alb", "aws::Elastic Load Balancing"),
    ("auto scaling", "aws::Amazon EC2 Auto Scaling"),
    ("ec2", "aws::Amazon EC2"),
    ("amazon rds", "aws::Amazon RDS"),
    ("rds", "aws::Amazon RDS"),
    ("dynamodb", "aws::Amazon DynamoDB"),
    ("route 53", "aws::Amazon Route 53"),
    ("route53", "aws::Amazon Route 53"),
    ("api gateway", "aws::Amazon API Gateway"),
    ("lambda", "aws::AWS Lambda"),
    ("cloudfront", "aws::Amazon CloudFront"),
    ("aws shield", "aws::AWS Shield"),
    ("cognito", "aws::Amazon Cognito"),
    ("s3", "aws::Amazon S3 on Outposts"),
    ("elastic beanstalk", "aws::AWS Elastic Beanstalk"),
    ("vpc", "aws::Amazon VPC Lattice"),
    # Security products (avoid mislabeling as cisco/azure)
    ("palo alto", "security::Palo Alto"),
    ("fortinet", "security::Fortinet"),
    ("claroty", "security::Claroty"),
    ("dragos", "security::Dragos"),
    ("splunk", "security::Splunk"),
    ("sophos", "security::Sophos"),
    # Industrial / OT
    ("controllogix", "plc::Allen Bradley"),
    ("allen-bradley", "plc::Allen Bradley"),
    ("siemens s7", "plc::Siemens S7"),
    ("ignition", "scada::Ignition"),
    ("wonderware", "scada::Wonderware"),
    ("osisoft", "scada::Osisoft Pi"),
    ("pi historian", "scada::Osisoft Pi"),
    ("sap", "sap::Erp"),
]

def correct_icons(diagram, registry_keys=None):
    """Override wrong icon keys for recognizable services. If registry_keys is
    provided, only assign keys that actually exist."""
    for node in diagram.get("nodes", []):
        label = (node.get("label") or "").lower()
        for needle, icon_key in ICON_NAME_MAP:
            if needle in label:
                if registry_keys is None or icon_key in registry_keys:
                    node["icon"] = icon_key
                break
    return diagram

def main_validate(diagram, domain="ot"):
    if not diagram or not isinstance(diagram, dict):
        return diagram
    diagram = correct_icons(diagram)
    industrial = domain in ("ot", "metal", "fmcg", "scada")
    if industrial:
        diagram = ensure_scada_master(diagram, domain)
        diagram = fix_field_flow(diagram)
        diagram = ensure_l3_l2_firewall(diagram, domain)
        diagram = ensure_ot_ad(diagram, domain)
        diagram = fix_historian_replication(diagram)
        diagram = fix_monitoring_feeds(diagram)
        diagram = ensure_siem_forwarding(diagram)
        if domain in ("ot", "metal", "scada"):
            diagram = ensure_safety_system(diagram, domain)
    return diagram