"use client";

import { useEffect, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Panel,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import ServiceNode from "./nodes/ServiceNode";

const nodeTypes = { service: ServiceNode };

const TIER_ORDER = ["edge", "load_balancing", "compute", "database", "security", "networking", "monitoring"];

const TIER_COLORS: Record<string, string> = {
  edge:            "#DD344C",
  load_balancing:  "#FF9900",
  compute:         "#FF9900",
  database:        "#3F48CC",
  security:        "#DD344C",
  networking:      "#8C4FFF",
  monitoring:      "#FF4F8B",
};

function buildNodesAndEdges(classified: any) {
  const nodes: any[] = [];
  const edges: any[] = [];
  const services = classified?.cheat_sheet?.aws_services || {};

  const tiers = TIER_ORDER.filter((t) => services[t]?.length > 0);
  const CANVAS_WIDTH = 900;
  const TIER_HEIGHT = 120;
  const START_Y = 60;

  tiers.forEach((tier, tierIndex) => {
    const tierServices: string[] = services[tier];
    const y = START_Y + tierIndex * TIER_HEIGHT;
    const totalWidth = tierServices.length * 200;
    const startX = (CANVAS_WIDTH - totalWidth) / 2;

    // Group background box
    nodes.push({
      id: `group-${tier}`,
      type: "default",
      position: { x: startX - 20, y: y - 30 },
      data: { label: "" },
      style: {
        width: totalWidth + 40,
        height: 90,
        background: `${TIER_COLORS[tier]}08`,
        border: `1px dashed ${TIER_COLORS[tier]}30`,
        borderRadius: "12px",
        zIndex: -1,
      },
      draggable: false,
      selectable: false,
    });

    // Tier label
    nodes.push({
      id: `label-${tier}`,
      type: "default",
      position: { x: startX - 10, y: y - 50 },
      data: { label: tier.replace("_", " ").toUpperCase() },
      style: {
        background: "transparent",
        border: "none",
        color: TIER_COLORS[tier],
        fontSize: "10px",
        fontWeight: 700,
        letterSpacing: "1px",
        padding: 0,
        boxShadow: "none",
      },
      draggable: false,
      selectable: false,
    });

    tierServices.forEach((service, svcIndex) => {
      const nodeId = `${tier}-${svcIndex}`;
      nodes.push({
        id: nodeId,
        type: "service",
        position: { x: startX + svcIndex * 200, y },
        data: { label: service, tier },
      });

      // Connect to previous tier
      if (tierIndex > 0) {
        const prevTier = tiers[tierIndex - 1];
        const prevServices: string[] = services[prevTier];
        const midPrev = Math.floor(prevServices.length / 2);
        const prevNodeId = `${prevTier}-${midPrev}`;
        if (svcIndex === Math.floor(tierServices.length / 2)) {
          edges.push({
            id: `e-${prevNodeId}-${nodeId}`,
            source: prevNodeId,
            target: nodeId,
            type: "smoothstep",
            markerEnd: { type: MarkerType.ArrowClosed, color: "#4B5563" },
            style: { stroke: "#4B5563", strokeWidth: 1.5 },
            animated: tier === "monitoring",
          });
        }
      }
    });
  });

  // Add on-prem nodes if OT/SCADA
  const appType = classified?.app_type;
  if (appType === "ot" || appType === "scada") {
    const onPremY = START_Y + tiers.length * TIER_HEIGHT + 40;

    nodes.push({
      id: "group-onprem",
      type: "default",
      position: { x: 20, y: onPremY - 30 },
      data: { label: "" },
      style: {
        width: 860,
        height: 100,
        background: "#00BCEB08",
        border: "1px dashed #00BCEB30",
        borderRadius: "12px",
        zIndex: -1,
      },
      draggable: false,
      selectable: false,
    });

    nodes.push({
      id: "label-onprem",
      type: "default",
      position: { x: 30, y: onPremY - 50 },
      data: { label: "ON-PREMISES / PLANT FLOOR" },
      style: {
        background: "transparent",
        border: "none",
        color: "#00BCEB",
        fontSize: "10px",
        fontWeight: 700,
        letterSpacing: "1px",
        padding: 0,
        boxShadow: "none",
      },
      draggable: false,
      selectable: false,
    });

    const onPremServices = appType === "scada"
      ? ["Cisco Router", "Cisco Firewall", "PLC", "SCADA Server", "HMI", "Historian"]
      : ["Cisco Router", "Cisco Switch", "Cisco Firewall", "PLC", "HMI"];

    onPremServices.forEach((service, i) => {
      const nodeId = `onprem-${i}`;
      nodes.push({
        id: nodeId,
        type: "service",
        position: { x: 40 + i * 160, y: onPremY },
        data: { label: service, tier: "on-prem" },
      });
    });

    // Connect Direct Connect to on-prem router
    const dcNode = nodes.find((n) => n.data?.label === "Direct Connect");
    if (dcNode) {
      edges.push({
        id: "e-dc-onprem",
        source: dcNode.id,
        target: "onprem-0",
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed, color: "#00BCEB" },
        style: { stroke: "#00BCEB", strokeWidth: 2, strokeDasharray: "6 3" },
        label: "Hybrid link",
        labelStyle: { fill: "#00BCEB", fontSize: 10 },
        labelBgStyle: { fill: "#0f0f1a" },
      });
    }
  }

  return { nodes, edges };
}

export default function ArchDiagram({ classified }: { classified: any }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (!classified) return;
    const { nodes: n, edges: e } = buildNodesAndEdges(classified);
    setNodes(n);
    setEdges(e);
  }, [classified]);

  return (
    <div style={{ width: "100%", height: "100%", background: "#0f0f1a", borderRadius: "12px" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3}
        maxZoom={2}
      >
        <Background color="#1a1a2e" gap={24} size={1} />
        <Controls style={{ background: "#1a1a2e", border: "1px solid #2a2a3e" }} />
        <MiniMap
          style={{ background: "#1a1a2e", border: "1px solid #2a2a3e" }}
          nodeColor="#FF9900"
        />
        <Panel position="top-right">
          <div style={{
            background: "#1a1a2e",
            border: "1px solid #2a2a3e",
            borderRadius: "8px",
            padding: "8px 12px",
            fontSize: "11px",
            color: "#9CA3AF",
          }}>
            {classified?.app_type?.toUpperCase()} — {classified?.cloud?.toUpperCase()}
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}
