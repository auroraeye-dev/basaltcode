import re

path = "/Users/SatvikMishra/Desktop/basaltcode/backend/diagram_generator.py"
with open(path) as f:
    content = f.read()

# Add "cells" to the OUTPUT FORMAT in the system prompt, after the zones array
# Find the zones array closing in the format block and add cells after it
zones_block = '''  "zones": [
    {{
      "id": "zone_id",
      "label": "Zone Label",
      "type": "cloud or onprem or dmz or safety or enterprise",
      "color": "blue or grey or orange or red or purple",
      "nodes": ["node_id_list"]
    }}
  ]
}}"""'''

new_block = '''  "zones": [
    {{
      "id": "zone_id",
      "label": "Zone Label",
      "type": "cloud or onprem or dmz or safety or enterprise",
      "color": "blue or grey or orange or red or purple",
      "nodes": ["node_id_list"]
    }}
  ],
  "cells": [
    {{
      "id": "cell_id",
      "label": "Production Cell Name (e.g. Body Shop, Paint Shop, Packaging Line)",
      "nodes": ["node_id_list — the L2/L1/L0 nodes belonging to THIS cell"]
    }}
  ]
}}

CELL/AREA ZONES (IMPORTANT):
- When a facility naturally has multiple parallel production areas (automotive: Body Shop / Paint Shop / Final Assembly; FMCG: Mixing / Filling / Packaging; metal: Furnace / Casting / Rolling), split Levels 2/1/0 into CELLS.
- Each cell is a vertical mini-stack: its own HMI/SCADA (L2), its own PLC (L1), its own field devices (L0).
- Put each lower-level node in BOTH its zone (level_2/level_1/level_0) AND its cell (via the cells array).
- Use job-specific equipment per cell: weld robots in body shop, paint robots in paint shop, conveyors in assembly.
- If the system has only ONE production area or is a simple network, leave "cells" as an empty array [].
- Upper levels (Enterprise, DMZ, Level 3) are NEVER split into cells — they stay shared."""'''

if zones_block in content:
    content = content.replace(zones_block, new_block)
    print("output format updated with cells")
else:
    print("WARNING: zones block not found exactly")

with open(path, "w") as f:
    f.write(content)
print("DONE")