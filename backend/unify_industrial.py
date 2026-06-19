import re
path = "/Users/SatvikMishra/Desktop/basaltcode/backend/diagram_generator.py"
with open(path) as f:
    content = f.read()

# Find the full OT rule text (between "ot": """ and the closing """,)
m = re.search(r'    "ot": """(.*?)""",\n', content, flags=re.DOTALL)
if not m:
    print("ERROR: could not find ot rule")
    exit()
ot_body = m.group(1)

# Replace the fmcg, metal, scada blocks each with the OT body
for domain in ["fmcg", "metal", "scada"]:
    pattern = r'    "' + domain + r'": """.*?""",\n'
    replacement = '    "' + domain + '": """' + ot_body + '""",\n'
    new_content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)
    if new_content != content:
        content = new_content
        print(f"{domain} now uses OT Purdue rules")
    else:
        print(f"WARNING: {domain} not replaced")

with open(path, "w") as f:
    f.write(content)
print("DONE")