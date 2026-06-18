path = "/Users/SatvikMishra/Desktop/basaltcode/backend/diagram_generator.py"
with open(path) as f:
    content = f.read()

# Strengthen the cell instructions: EVERY L2/L1/L0 node must be in a cell, including per-cell HMI/SCADA
old = '''- Put each lower-level node in BOTH its zone (level_2/level_1/level_0) AND its cell (via the cells array).
- Use job-specific equipment per cell: weld robots in body shop, paint robots in paint shop, conveyors in assembly.
- If the system has only ONE production area or is a simple network, leave "cells" as an empty array [].
- Upper levels (Enterprise, DMZ, Level 3) are NEVER split into cells — they stay shared.'''

new = '''- CRITICAL: when you use cells, EVERY node at level_2, level_1, and level_0 MUST be assigned to exactly one cell. Leave NONE unassigned.
- Each cell should contain its OWN L2 HMI/SCADA, its OWN L1 PLC, and its OWN L0 field devices. Give each cell a full vertical stack.
- Example per cell: Body Shop = {L2: HMI, L1: ControlLogix PLC, L0: Weld Robots + Sensors}; Paint Shop = {L2: HMI, L1: PLC, L0: Paint Robots + Booth}; Assembly = {L2: HMI, L1: PLC, L0: Conveyor + Torque Tools}.
- Put each lower-level node in BOTH its zone (level_2/level_1/level_0) AND its cell (via the cells array). Every level_2/1/0 node id must appear in some cell's nodes list.
- Shared supervisory systems (Area Historian, plant-wide SCADA) can stay at level_3 instead — do NOT leave them dangling at level_2 outside a cell.
- Use job-specific equipment per cell: weld robots in body shop, paint robots in paint shop, conveyors in assembly.
- If the system has only ONE production area or is a simple network, leave "cells" as an empty array [].
- Upper levels (Enterprise, DMZ, Level 3) are NEVER split into cells — they stay shared.'''

if old in content:
    content = content.replace(old, new)
    print("cell rules strengthened")
else:
    print("WARNING: old block not found")

with open(path, "w") as f:
    f.write(content)
print("DONE")