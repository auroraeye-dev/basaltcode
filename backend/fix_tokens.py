path = "/Users/SatvikMishra/Desktop/basaltcode/backend/diagram_generator.py"
with open(path) as f:
    content = f.read()

# 1. Raise max_tokens for generation
if "max_tokens=3000" in content:
    content = content.replace("max_tokens=3000", "max_tokens=8000")
    print("max_tokens 3000 -> 8000")
elif "max_tokens=4000" in content:
    content = content.replace("max_tokens=4000", "max_tokens=8000")
    print("max_tokens 4000 -> 8000")
else:
    print("WARNING: max_tokens line not found, check manually")

with open(path, "w") as f:
    f.write(content)
print("DONE")