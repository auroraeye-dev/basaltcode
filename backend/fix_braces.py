path = "/Users/SatvikMishra/Desktop/basaltcode/backend/diagram_generator.py"
with open(path) as f:
    content = f.read()

# The example line has single braces that break .format(). Double them.
bad = "Example per cell: Body Shop = {L2: HMI, L1: ControlLogix PLC, L0: Weld Robots + Sensors}; Paint Shop = {L2: HMI, L1: PLC, L0: Paint Robots + Booth}; Assembly = {L2: HMI, L1: PLC, L0: Conveyor + Torque Tools}."
good = "Example per cell: Body Shop = [L2: HMI, L1: ControlLogix PLC, L0: Weld Robots + Sensors]; Paint Shop = [L2: HMI, L1: PLC, L0: Paint Robots + Booth]; Assembly = [L2: HMI, L1: PLC, L0: Conveyor + Torque Tools]."

if bad in content:
    content = content.replace(bad, good)
    print("fixed braces in example")
else:
    print("exact line not found, trying generic brace-safe replace")
    # Fallback: replace any remaining single-brace cell examples
    import re
    content = content.replace("{L2:", "[L2:").replace("{L1:", "[L1:")

with open(path, "w") as f:
    f.write(content)
print("DONE")