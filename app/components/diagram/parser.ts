import { Node, Edge, MarkerType } from "@xyflow/react";

const ZONE_COLORS: Record<string, string> = {
  cloud: "#1a3a5c",
  onprem: "#1a2a1a",
  dmz: "#3a2a0a",
  safety: "#3a0a0a",
  enterprise: "#2a1a3a",
  default: "#1a1a2a",
};

const ZONE_BORDERS: Record<string, string> = {
  cloud: "#378ADD",
  onprem: "#4CAF50",
  dmz: "#FF9800",
  safety: "#F44336",
  enterprise: "#9C27B0",
  default: "#555577",
};

export function parseDiagramToFlow(diagram: any): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  if (!diagram) return { nodes, edges };

  const zoneMap: Record<string, any> = {};
  (diagram.zones || []).forEach((z: any) => {
    zoneMap[z.id] = z;
  });

  // Build zone group nodes
  const zoneNodeCounts: Record<string, number> = {};
  (diagram.nodes || []).forEach((n: any) => {
    if (n.zone) zoneNodeCounts[n.zone] = (zoneNodeCounts[n.zone] || 0) + 1;
  });

  const zonePositions: Record<string, { x: number; y: number; width: number; height: number }> = {};
  const ZONE_ORDER = ["level_4_5", "level_4", "enterprise", "dmz", "level_3", "level_2", "level_1", "level_0", "cloud", "safety", "onprem"];

  const sortedZones = (diagram.zones || []).sort((a: any, b: any) => {
    const ai = ZONE_ORDER.indexOf(a.id);
    const bi = ZONE_ORDER.indexOf(b.id);
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });

  sortedZones.forEach((zone: any, zIndex: number) => {
    const count = zoneNodeCounts[zone.id] || 1;
    const width = Math.max(count * 260, 400);
    const height = 170;
    const x = 40;
    const y = 60 + zIndex * 240;

    zonePositions[zone.id] = { x, y, width, height };

    nodes.push({
      id: `zone-${zone.id}`,
      type: "group",
      position: { x, y },
      data: { label: zone.label, type: zone.type, color: zone.color },
      style: {
        width,
        height,
        backgroundColor: ZONE_COLORS[zone.type] || ZONE_COLORS.default,
        border: `1.5px dashed ${ZONE_BORDERS[zone.type] || ZONE_BORDERS.default}`,
        borderRadius: "12px",
        zIndex: -1,
      },
    });

    // Zone label
    nodes.push({
      id: `zone-label-${zone.id}`,
      type: "default",
      position: { x: x + 12, y: y - 22 },
      data: { label: zone.label },
      style: {
        background: "transparent",
        border: "none",
        color: ZONE_BORDERS[zone.type] || ZONE_BORDERS.default,
        fontSize: "11px",
        fontWeight: 700,
        letterSpacing: "0.5px",
        padding: 0,
        boxShadow: "none",
        pointerEvents: "none",
      },
      draggable: false,
      selectable: false,
    });
  });

  // Build service nodes
  const zoneNodeIndex: Record<string, number> = {};
  (diagram.nodes || []).forEach((node: any) => {
    const zoneId = node.zone || "default";
    const zonePos = zonePositions[zoneId] || { x: 100, y: 100, width: 400, height: 140 };
    const idx = zoneNodeIndex[zoneId] || 0;
    zoneNodeIndex[zoneId] = idx + 1;

    const x = zonePos.x + 30 + idx * 250;
    const y = zonePos.y + 50;

    nodes.push({
      id: node.id,
      type: "iconNode",
      position: { x, y },
      data: {
        label: node.label,
        icon: node.icon,
        description: node.description,
        zone: node.zone,
      },
      parentId: `zone-${zoneId}`,
      extent: "parent",
    });
  });

  // Build edges
  (diagram.edges || []).forEach((edge: any) => {
    edges.push({
      id: edge.id || `e-${edge.from}-${edge.to}`,
      source: edge.from,
      target: edge.to,
      label: edge.label || "",
      type: "smoothstep",
      animated: edge.style === "animated",
      style: {
        stroke: edge.style === "dashed" ? "#888" : "#4A9EFF",
        strokeWidth: 1.5,
        strokeDasharray: edge.style === "dashed" ? "5 3" : undefined,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: edge.style === "dashed" ? "#888" : "#4A9EFF",
        width: 15,
        height: 15,
      },
      labelStyle: { fill: "#9CA3AF", fontSize: 10, fontWeight: 500 },
      labelBgStyle: { fill: "#0f0f1a", fillOpacity: 0.8 },
      labelBgPadding: [4, 6] as [number, number],
      labelBgBorderRadius: 4,
    });
  });

  return { nodes, edges };
}