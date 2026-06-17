"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  ReactFlow, Background, Controls, MiniMap, Panel,
  useNodesState, useEdgesState, addEdge, MarkerType,
  reconnectEdge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import IconNode from "./IconNode";
import ZoneGroup from "./ZoneGroup";
import { parseDiagramToFlow } from "./parser";
import { toPng, toSvg } from "html-to-image";

const nodeTypes = { iconNode: IconNode, zoneGroup: ZoneGroup };

export default function DiagramCanvas({ diagram, title }: { diagram: any; title?: string }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [showAdd, setShowAdd] = useState(false);
  const wrapper = useRef<HTMLDivElement>(null);
  const edgeReconnectSuccessful = useRef(true);

  useEffect(() => {
    if (!diagram) return;
    const { nodes: n, edges: e } = parseDiagramToFlow(diagram);
    setNodes(n);
    setEdges(e);
  }, [diagram]);

  const onConnect = useCallback((params: any) => {
    setEdges((eds) => addEdge({
      ...params,
      type: "smoothstep",
      style: { stroke: "#8FB4E8", strokeWidth: 1.5 },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#8FB4E8", width: 14, height: 14 },
    }, eds));
  }, [setEdges]);

  const onReconnectStart = useCallback(() => { edgeReconnectSuccessful.current = false; }, []);
  const onReconnect = useCallback((oldEdge: any, newConn: any) => {
    edgeReconnectSuccessful.current = true;
    setEdges((els) => reconnectEdge(oldEdge, newConn, els));
  }, [setEdges]);
  const onReconnectEnd = useCallback((_: any, edge: any) => {
    if (!edgeReconnectSuccessful.current) setEdges((eds) => eds.filter((e) => e.id !== edge.id));
    edgeReconnectSuccessful.current = true;
  }, [setEdges]);

  // Double-click node to rename
  const onNodeDoubleClick = useCallback((_: any, node: any) => {
    if (node.type !== "iconNode") return;
    const newLabel = prompt("Rename node:", node.data.label);
    if (newLabel) {
      setNodes((nds) => nds.map((n) => n.id === node.id ? { ...n, data: { ...n.data, label: newLabel } } : n));
    }
  }, [setNodes]);

  // Delete key removes selected
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Delete" || e.key === "Backspace") {
        const tag = (e.target as HTMLElement)?.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA") return;
        setNodes((nds) => nds.filter((n) => !n.selected));
        setEdges((eds) => eds.filter((ed) => !ed.selected));
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [setNodes, setEdges]);

  const addNode = (icon: string, label: string) => {
    const id = `n-${Date.now()}`;
    setNodes((nds) => [...nds, {
      id, type: "iconNode", position: { x: 200, y: 200 },
      data: { label, icon, accent: "#8FB4E8", description: "" },
    }]);
    setShowAdd(false);
  };

  const exportPng = async () => {
    if (!wrapper.current) return;
    const el = wrapper.current.querySelector(".react-flow__viewport") as HTMLElement;
    if (!el) return;
    const dataUrl = await toPng(el, { backgroundColor: "#08090C", pixelRatio: 2 });
    const a = document.createElement("a");
    a.download = `basalt-${Date.now()}.png`;
    a.href = dataUrl;
    a.click();
  };

  const btnStyle: React.CSSProperties = {
    background: "#11141B", border: "1px solid #2A3038", color: "#C8D2E1",
    borderRadius: 8, padding: "7px 12px", fontSize: 12, cursor: "pointer",
    display: "flex", alignItems: "center", gap: 6, fontWeight: 500,
  };

  return (
    <div ref={wrapper} style={{ width: "100%", height: "100%", background: "#08090C", borderRadius: 14, overflow: "hidden", position: "relative" }}>
      <ReactFlow
        nodes={nodes} edges={edges}
        onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onReconnect={onReconnect} onReconnectStart={onReconnectStart} onReconnectEnd={onReconnectEnd}
        onNodeDoubleClick={onNodeDoubleClick}
        nodeTypes={nodeTypes}
        fitView fitViewOptions={{ padding: 0.12 }}
        minZoom={0.15} maxZoom={2.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#161A22" gap={26} size={1} />
        <Controls style={{ background: "#11141B", border: "1px solid #2A3038", borderRadius: 8 }} />
        <MiniMap style={{ background: "#0B0D12", border: "1px solid #2A3038", borderRadius: 8 }}
          nodeColor={(n) => n.type === "zoneGroup" ? "#1a1f29" : "#8FB4E8"} maskColor="rgba(0,0,0,0.7)" />

        <Panel position="top-left">
          <div style={{ display: "flex", gap: 8 }}>
            <button style={btnStyle} onClick={() => setShowAdd((s) => !s)}>+ Add node</button>
            <button style={btnStyle} onClick={exportPng}>↓ Export PNG</button>
          </div>
          {showAdd && (
            <div style={{ marginTop: 8, background: "#0B0D12", border: "1px solid #2A3038", borderRadius: 10, padding: 10, width: 240 }}>
              <div style={{ fontSize: 10, color: "#6A7585", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 }}>Quick add</div>
              {[
                ["generic::Server", "Server"], ["generic::Database", "Database"],
                ["generic::Firewall", "Firewall"], ["plc::Allen Bradley", "PLC"],
                ["scada::Ignition", "SCADA"], ["industrial::Sensor", "Sensor"],
                ["security::Claroty", "OT Monitor"], ["sap::Erp", "SAP ERP"],
              ].map(([icon, label]) => (
                <div key={icon} onClick={() => addNode(icon, label)}
                  style={{ padding: "7px 9px", fontSize: 12, color: "#C8D2E1", cursor: "pointer", borderRadius: 6 }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#1A1F29")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                  {label}
                </div>
              ))}
            </div>
          )}
        </Panel>

        {title && (
          <Panel position="top-right">
            <div style={{ background: "#11141B", border: "1px solid #2A3038", borderRadius: 8, padding: "8px 14px", fontSize: 12, color: "#C8D2E1", maxWidth: 240, fontWeight: 500 }}>
              {title}
            </div>
          </Panel>
        )}
      </ReactFlow>
    </div>
  );
}
