path = "/Users/SatvikMishra/Desktop/basaltcode/backend/diagram_generator.py"
with open(path) as f:
    content = f.read()

# Add a strict balance rule to the cell instructions
anchor = "- CRITICAL: when you use cells, EVERY node at level_2, level_1, and level_0 MUST be assigned to exactly one cell. Leave NONE unassigned."

strict = """- CRITICAL: when you use cells, EVERY node at level_2, level_1, and level_0 MUST be assigned to exactly one cell. Leave NONE unassigned.
- BALANCE RULE: every cell MUST have the SAME complete vertical stack — do NOT dump most nodes into one cell. Each cell gets: its own HMI or local SCADA (level_2), its own PLC (level_1), its own sensors AND actuators (level_0). If you create 3 cells, you create roughly 3x4 = 12 lower-level nodes, 4 per cell.
- Do NOT leave any cell with fewer nodes than the others. Body Shop, Paint Shop, and Assembly must each be a full stack.
- Plant-wide shared systems (one site-wide SCADA, one Area Historian) belong at level_3, NOT inside a single cell and NOT dangling at level_2."""

if anchor in content:
    content = content.replace(anchor, strict)
    print("balance rule added")
else:
    print("WARNING anchor not found")

with open(path, "w") as f:
    f.write(content)
print("DONE")