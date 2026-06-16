"use client";

import { useEffect, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Panel,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import IconNode from "./IconNode";
import { parseDiagramToFlow } from "./parser";

const nodeTypes = { iconNode: IconNode };

export default function DiagramCanvas({ diagram, title }: { diagram: any; title?: string }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (!diagram) return;
    const { nodes: n, edges: e } = parseDiagramToFlow(diagram);
    setNodes(n);
    setEdges(e);
  }, [diagram]);

  return (
    <div style={{ width: "100%", height: "100%", background: "#0a0a14", borderRadius: "12px", overflow: "hidden" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.2}
        maxZoom={2}
        defaultEdgeOptions={{ type: "smoothstep" }}
      >
        <Background color="#1a1a2e" gap={24} size={1} />
        <Controls
          style={{
            background: "#111827",
            border: "1px solid #2a2a3e",
            borderRadius: "8px",
          }}
        />
        <MiniMap
          style={{
            background: "#111827",
            border: "1px solid #2a2a3e",
            borderRadius: "8px",
          }}
          nodeColor="#4A9EFF"
          maskColor="rgba(0,0,0,0.6)"
        />
        {title && (
          <Panel position="top-right">
            <div style={{
              background: "#111827",
              border: "1px solid #2a2a3e",
              borderRadius: "8px",
              padding: "6px 12px",
              fontSize: "11px",
              color: "#9CA3AF",
              maxWidth: "200px",
            }}>
              {title}
            </div>
          </Panel>
        )}
      </ReactFlow>
    </div>
  );
}
