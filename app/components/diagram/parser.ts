import { Node, Edge, MarkerType } from "@xyflow/react";

const ZONE_THEME: Record<string, { bg: string; border: string; accent: string }> = {
  cloud:      { bg: "rgba(91,155,213,0.06)",  border: "#5B9BD5", accent: "#7BB0E8" },
  enterprise: { bg: "rgba(123,176,232,0.06)", border: "#6B8Fc4", accent: "#8FB4E8" },
  dmz:        { bg: "rgba(232,155,92,0.07)",  border: "#E89B5C", accent: "#F0A868" },
  onprem:     { bg: "rgba(200,210,225,0.04)", border: "#8A94A6", accent: "#C8D2E1" },
  safety:     { bg: "rgba(226,75,74,0.07)",   border: "#E24B4A", accent: "#F09595" },
  cell:       { bg: "rgba(143,180,232,0.05)", border: "#5E6B82", accent: "#9DB4D8" },
  default:    { bg: "rgba(200,210,225,0.04)", border: "#6A7585", accent: "#A8B2C2" },
};

const UPPER_ORDER = ["level_5", "level_4_5", "level_4", "enterprise", "cloud", "dmz", "level_3"];
const LOWER_LEVELS = ["level_2", "level_1", "level_0"];

const BAND_X = 80;
const BAND_WIDTH = 1500;
const BAND_TOP = 80;
const BAND_GAP = 55;
const HEADER_H = 46;
const NODE_W = 180;
const NODE_H = 78;
const NODE_GAP_X = 36;
const NODE_ROW_GAP = 26;
const SIDE_PAD = 40;

// Cell layout constants
const CELL_GAP = 28;
const CELL_INNER_PAD = 18;
const CELL_NODE_VGAP = 24;
const CELL_HEADER_H = 40;

function makeNode(node: any, x: number, y: number, accent: string): Node {
  return {
    id: node.id, type: "iconNode", position: { x, y },
    data: { label: node.label, icon: node.icon, description: node.description, accent },
  };
}

function fullWidthBand(
  zone: any, zNodes: any[], cursorY: number, perRow: number, nodes: Node[]
): number {
  if (zNodes.length === 0) return cursorY;
  const rows = Math.max(1, Math.ceil(zNodes.length / perRow));
  const bandH = HEADER_H + rows * NODE_H + (rows - 1) * NODE_ROW_GAP + 28;
  const theme = ZONE_THEME[zone.type] || ZONE_THEME.default;

  nodes.push({
    id: `zone-${zone.id}`, type: "zoneGroup",
    position: { x: BAND_X, y: cursorY },
    data: { label: zone.label, theme },
    style: { width: BAND_WIDTH, height: bandH, zIndex: -10 },
    draggable: false, selectable: false,
  });

  zNodes.forEach((node: any, i: number) => {
    const row = Math.floor(i / perRow);
    const countThisRow = Math.min(perRow, zNodes.length - row * perRow);
    const rowWidth = countThisRow * NODE_W + (countThisRow - 1) * NODE_GAP_X;
    const startX = BAND_X + (BAND_WIDTH - rowWidth) / 2;
    const x = startX + (i % perRow) * (NODE_W + NODE_GAP_X);
    const y = cursorY + HEADER_H + 8 + row * (NODE_H + NODE_ROW_GAP);
    nodes.push(makeNode(node, x, y, theme.accent));
  });

  return cursorY + bandH + BAND_GAP;
}

export function parseDiagramToFlow(diagram: any): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  if (!diagram) return { nodes, edges };

  const cells = diagram.cells || [];
  const hasCells = cells.length > 0;

  const nodeById: Record<string, any> = {};
  (diagram.nodes || []).forEach((n: any) => { nodeById[n.id] = n; });

  const cellNodeIds = new Set<string>();
  cells.forEach((c: any) => (c.nodes || []).forEach((id: string) => cellNodeIds.add(id)));

  const nodesByZone: Record<string, any[]> = {};
  (diagram.nodes || []).forEach((n: any) => {
    const z = n.zone || "default";
    (nodesByZone[z] = nodesByZone[z] || []).push(n);
  });

  const zonesById: Record<string, any> = {};
  (diagram.zones || []).forEach((z: any) => { zonesById[z.id] = z; });

  const perRow = Math.max(1, Math.floor((BAND_WIDTH - SIDE_PAD * 2 + NODE_GAP_X) / (NODE_W + NODE_GAP_X)));
  let cursorY = BAND_TOP;

  // 1. UPPER ZONES
  const upperZones = (diagram.zones || [])
    .filter((z: any) => UPPER_ORDER.includes(z.id))
    .sort((a: any, b: any) => UPPER_ORDER.indexOf(a.id) - UPPER_ORDER.indexOf(b.id));

  upperZones.forEach((zone: any) => {
    const zNodes = (nodesByZone[zone.id] || []).filter((n: any) => !cellNodeIds.has(n.id));
    cursorY = fullWidthBand(zone, zNodes, cursorY, perRow, nodes);
  });

  // 2a. Shared lower-level nodes not assigned to any cell -> one clean band (above cells)
  if (hasCells) {
    const orphans: any[] = [];
    LOWER_LEVELS.forEach((lvlId) => {
      (nodesByZone[lvlId] || []).forEach((n: any) => {
        if (!cellNodeIds.has(n.id)) orphans.push(n);
      });
    });
    if (orphans.length > 0) {
      const sharedZone = { id: "shared_ot", label: "Shared OT Systems", type: "onprem" };
      cursorY = fullWidthBand(sharedZone, orphans, cursorY, perRow, nodes);
    }
  }

  // 2. CELL/AREA ZONES
  if (hasCells) {
    const cellCount = cells.length;
    const cellWidth = Math.min(
      400,
      (BAND_WIDTH - SIDE_PAD * 2 - (cellCount - 1) * CELL_GAP) / cellCount
    );

    // Compute each cell's ordered nodes and the max stack height
    const LEVEL_ORDER = ["level_2", "level_1", "level_0"];
    const cellsOrdered = cells.map((cell: any) => {
      const cn = (cell.nodes || [])
        .map((id: string) => nodeById[id])
        .filter(Boolean)
        .sort((a: any, b: any) => LEVEL_ORDER.indexOf(a.zone) - LEVEL_ORDER.indexOf(b.zone));
      return { ...cell, ordered: cn };
    });
    const maxNodes = Math.max(1, ...cellsOrdered.map((c: any) => c.ordered.length));

    const cellInnerH = CELL_HEADER_H + CELL_INNER_PAD + maxNodes * NODE_H + (maxNodes - 1) * CELL_NODE_VGAP + CELL_INNER_PAD;
    const containerH = HEADER_H + 12 + cellInnerH + 24;

    // Outer container
    nodes.push({
      id: "zone-cellarea", type: "zoneGroup",
      position: { x: BAND_X, y: cursorY },
      data: { label: "Cell / Area Zones — Levels 2 / 1 / 0", theme: ZONE_THEME.onprem },
      style: { width: BAND_WIDTH, height: containerH, zIndex: -10 },
      draggable: false, selectable: false,
    });

    const cellsStartY = cursorY + HEADER_H + 6;
    // Center the row of cells inside the container
    const totalCellsWidth = cellCount * cellWidth + (cellCount - 1) * CELL_GAP;
    const cellsStartX = BAND_X + (BAND_WIDTH - totalCellsWidth) / 2;

    cellsOrdered.forEach((cell: any, ci: number) => {
      const cellX = cellsStartX + ci * (cellWidth + CELL_GAP);

      // Inner cell box
      nodes.push({
        id: `cell-${cell.id}`, type: "zoneGroup",
        position: { x: cellX, y: cellsStartY },
        data: { label: cell.label, theme: ZONE_THEME.cell },
        style: { width: cellWidth, height: cellInnerH, zIndex: -5 },
        draggable: false, selectable: false,
      });

      // Stack the cell's nodes vertically, centered in the cell
      cell.ordered.forEach((node: any, ni: number) => {
        const x = cellX + (cellWidth - NODE_W) / 2;
        const y = cellsStartY + CELL_HEADER_H + CELL_INNER_PAD + ni * (NODE_H + CELL_NODE_VGAP);
        nodes.push(makeNode(node, x, y, ZONE_THEME.cell.accent));
      });
    });

    cursorY += containerH + BAND_GAP;
  }

  // 3. (handled above as Shared OT Systems band)

  // Edges
  (diagram.edges || []).forEach((edge: any) => {
    const dashed = edge.style === "dashed";
    edges.push({
      id: edge.id || `e-${edge.from}-${edge.to}`,
      source: edge.from, target: edge.to, label: edge.label || "",
      type: "smoothstep", animated: edge.style === "animated",
      style: { stroke: dashed ? "#6A7585" : "#8FB4E8", strokeWidth: 1.5, strokeDasharray: dashed ? "5 4" : undefined },
      markerEnd: { type: MarkerType.ArrowClosed, color: dashed ? "#6A7585" : "#8FB4E8", width: 14, height: 14 },
      labelStyle: { fill: "#C8D2E1", fontSize: 10, fontWeight: 500 },
      labelBgStyle: { fill: "#0B0D12", fillOpacity: 0.9 },
      labelBgPadding: [5, 7] as [number, number], labelBgBorderRadius: 5,
    });
  });

  return { nodes, edges };
}