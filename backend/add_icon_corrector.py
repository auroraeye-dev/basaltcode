path = "/Users/SatvikMishra/Desktop/basaltcode/backend/validator.py"
with open(path) as f:
    content = f.read()

corrector = '''

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
'''

# insert before main_validate
content = content.replace("def main_validate(", corrector + "\ndef main_validate(", 1)

# call it at the start of main_validate (runs for ALL domains)
old = '''def main_validate(diagram, domain="ot"):
    if not diagram or not isinstance(diagram, dict):
        return diagram'''
new = '''def main_validate(diagram, domain="ot"):
    if not diagram or not isinstance(diagram, dict):
        return diagram
    diagram = correct_icons(diagram)'''
content = content.replace(old, new)

with open(path, "w") as f:
    f.write(content)

import ast
ast.parse(content)
print("icon corrector added and syntax OK")