import { Node, Edge, MarkerType } from "@xyflow/react";

// Basalt brand theme — derived from the logo (black field, chrome lines, blue IT / amber OT)
const ZONE_THEME: Record<string, { bg: string; border: string; accent: string }> = {
  cloud:      { bg: "rgba(91,155,213,0.06)",  border: "#5B9BD5", accent: "#7BB0E8" },
  enterprise: { bg: "rgba(123,176,232,0.06)", border: "#6B8Fc4", accent: "#8FB4E8" },
  dmz:        { bg: "rgba(232,155,92,0.07)",  border: "#E89B5C", accent: "#F0A868" },
  onprem:     { bg: "rgba(200,210,225,0.04)", border: "#8A94A6", accent: "#C8D2E1" },
  safety:     { bg: "rgba(226,75,74,0.07)",   border: "#E24B4A", accent: "#F09595" },
  default:    { bg: "rgba(200,210,225,0.04)", border: "#6A7585", accent: "#A8B2C2" },
};

// Full-width band ordering, top (enterprise/IT) to bottom (field/OT)
const ZONE_ORDER = [
  "level_5", "level_4_5", "level_4", "enterprise", "cloud",
  "dmz",
  "level_3", "level_2", "level_1", "level_0",
  "safety", "onprem",
];

const BAND_X = 80;
const BAND_WIDTH = 1400;
const BAND_TOP = 80;
const BAND_GAP = 60;
const HEADER_H = 44;
const NODE_W = 180;
const NODE_H = 78;
const NODE_GAP_X = 40;
const NODE_ROW_GAP = 28;
const SIDE_PAD = 40;

export function parseDiagramToFlow(diagram: any): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  if (!diagram) return { nodes, edges };

  const zones = (diagram.zones || []).slice().sort((a: any, b: any) => {
    const ai = ZONE_ORDER.indexOf(a.id); const bi = ZONE_ORDER.indexOf(b.id);
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });

  // Group nodes by zone
  const nodesByZone: Record<string, any[]> = {};
  (diagram.nodes || []).forEach((n: any) => {
    const z = n.zone || "default";
    (nodesByZone[z] = nodesByZone[z] || []).push(n);
  });

  // How many nodes fit per row inside a band
  const perRow = Math.max(1, Math.floor((BAND_WIDTH - SIDE_PAD * 2 + NODE_GAP_X) / (NODE_W + NODE_GAP_X)));

  let cursorY = BAND_TOP;

  zones.forEach((zone: any) => {
    const zNodes = nodesByZone[zone.id] || [];
    const rows = Math.max(1, Math.ceil(zNodes.length / perRow));
    const bandH = HEADER_H + rows * NODE_H + (rows - 1) * NODE_ROW_GAP + 28;
    const theme = ZONE_THEME[zone.type] || ZONE_THEME.default;

    // Band background
    nodes.push({
      id: `zone-${zone.id}`,
      type: "zoneGroup",
      position: { x: BAND_X, y: cursorY },
      data: { label: zone.label, type: zone.type, theme },
      style: { width: BAND_WIDTH, height: bandH, zIndex: -10 },
      draggable: false,
      selectable: false,
    });

    // Nodes laid out in centered rows
    zNodes.forEach((node: any, i: number) => {
      const row = Math.floor(i / perRow);
      const countThisRow = Math.min(perRow, zNodes.length - row * perRow);
      const rowWidth = countThisRow * NODE_W + (countThisRow - 1) * NODE_GAP_X;
      const startX = BAND_X + (BAND_WIDTH - rowWidth) / 2;
      const col = i % perRow;
      const x = startX + col * (NODE_W + NODE_GAP_X);
      const y = cursorY + HEADER_H + 8 + row * (NODE_H + NODE_ROW_GAP);

      nodes.push({
        id: node.id,
        type: "iconNode",
        position: { x, y },
        data: {
          label: node.label,
          icon: node.icon,
          description: node.description,
          zoneType: zone.type,
          accent: theme.accent,
        },
      });
    });

    cursorY += bandH + BAND_GAP;
  });

  // Edges
  (diagram.edges || []).forEach((edge: any) => {
    const dashed = edge.style === "dashed";
    edges.push({
      id: edge.id || `e-${edge.from}-${edge.to}`,
      source: edge.from,
      target: edge.to,
      label: edge.label || "",
      type: "smoothstep",
      animated: edge.style === "animated",
      style: {
        stroke: dashed ? "#6A7585" : "#8FB4E8",
        strokeWidth: 1.5,
        strokeDasharray: dashed ? "5 4" : undefined,
      },
      markerEnd: { type: MarkerType.ArrowClosed, color: dashed ? "#6A7585" : "#8FB4E8", width: 14, height: 14 },
      labelStyle: { fill: "#C8D2E1", fontSize: 10, fontWeight: 500 },
      labelBgStyle: { fill: "#0B0D12", fillOpacity: 0.9 },
      labelBgPadding: [5, 7] as [number, number],
      labelBgBorderRadius: 5,
    });
  });

  return { nodes, edges };
}