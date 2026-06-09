CHEAT_SHEETS = {
    "pharma": {
        "compliance_pool": ["FDA 21 CFR Part 11", "GAMP5", "GMP", "EU Annex 11"],
        "aws_services": {
            "edge": ["CloudFront", "AWS WAF"],
            "compute": ["EC2 Auto Scaling", "EKS"],
            "database": ["Aurora PostgreSQL", "RDS"],
            "security": ["KMS", "CloudTrail", "GuardDuty"],
            "networking": ["VPC", "Private Subnets", "PrivateLink"],
            "monitoring": ["CloudWatch", "Security Hub"]
        },
        "must_have": ["Audit logging", "Electronic signatures", "Data integrity"]
    },
    "ot": {
        "compliance_pool": ["IEC 62443", "NIST SP 800-82", "ISA-95"],
        "aws_services": {
            "edge": ["AWS IoT Greengrass", "AWS WAF"],
            "compute": ["EC2", "AWS IoT Core"],
            "database": ["Aurora PostgreSQL", "Timestream"],
            "security": ["KMS", "GuardDuty", "CloudTrail"],
            "networking": ["VPC", "Private Subnets", "Direct Connect"],
            "monitoring": ["CloudWatch", "AWS IoT Analytics"]
        },
        "must_have": ["Network segmentation", "DMZ", "Firewall", "OT monitoring"]
    },
    "scada": {
        "compliance_pool": ["IEC 62443", "NIST SP 800-82", "NERC CIP"],
        "aws_services": {
            "edge": ["AWS IoT Greengrass"],
            "compute": ["EC2", "AWS IoT Core"],
            "database": ["Timestream", "DynamoDB"],
            "security": ["KMS", "GuardDuty", "CloudTrail"],
            "networking": ["VPC", "Private Subnets", "Direct Connect"],
            "monitoring": ["CloudWatch"]
        },
        "must_have": ["Air gap or DMZ", "Unidirectional data flow", "Historian", "PLC hardening"]
    },
    "fmcg": {
        "compliance_pool": ["GS1", "ISO 22000", "GDPR"],
        "aws_services": {
            "edge": ["CloudFront", "AWS WAF"],
            "compute": ["EC2 Auto Scaling", "EKS"],
            "database": ["Aurora MySQL", "ElastiCache Redis"],
            "security": ["KMS", "GuardDuty"],
            "networking": ["VPC", "Private Subnets"],
            "monitoring": ["CloudWatch"]
        },
        "must_have": ["ERP integration", "Supply chain visibility", "CDN"]
    },
    "metal": {
        "compliance_pool": ["ISO 50001", "IEC 62443"],
        "aws_services": {
            "edge": ["AWS IoT Greengrass"],
            "compute": ["EC2 Auto Scaling", "EKS"],
            "database": ["Aurora PostgreSQL", "Timestream"],
            "security": ["KMS", "GuardDuty", "CloudTrail"],
            "networking": ["VPC", "Private Subnets", "Direct Connect"],
            "monitoring": ["CloudWatch"]
        },
        "must_have": ["Plant network segmentation", "MES system", "ERP integration"]
    },
    "general": {
        "compliance_pool": ["SOC 2", "GDPR", "ISO 27001"],
        "aws_services": {
            "edge": ["CloudFront", "AWS WAF"],
            "compute": ["EC2 Auto Scaling", "Lambda"],
            "database": ["Aurora PostgreSQL", "DynamoDB"],
            "security": ["KMS", "GuardDuty"],
            "networking": ["VPC", "Private Subnets"],
            "monitoring": ["CloudWatch"]
        },
        "must_have": ["Auth", "Monitoring", "Backups"]
    }
}

APP_TYPE_ALIASES = {
    "pharmaceutical": "pharma",
    "drug": "pharma",
    "plant": "ot",
    "industrial": "ot",
    "operational technology": "ot",
    "control system": "scada",
    "plc": "scada",
    "dcs": "scada",
    "supply chain": "fmcg",
    "consumer goods": "fmcg",
    "factory": "metal",
    "manufacturing": "metal",
}

def classify(parsed: dict) -> dict:
    app_type = parsed.get("app_type", "general").lower()
    app_type = APP_TYPE_ALIASES.get(app_type, app_type)
    if app_type not in CHEAT_SHEETS:
        app_type = "general"
        matched = False
    else:
        matched = True
    return {
        "app_type": app_type,
        "matched": matched,
        "cheat_sheet": CHEAT_SHEETS[app_type],
        "cloud": parsed.get("cloud", "aws"),
        "compliance": parsed.get("compliance", []),
        "scale": parsed.get("scale", "unspecified"),
        "budget": parsed.get("budget", "unspecified"),
        "ambiguous_fields": parsed.get("ambiguous_fields", [])
    }
