"use client";
import { Handle, Position } from "@xyflow/react";
import { useState } from "react";

const ICON_BASE = "/icons";

function getIconUrl(iconKey: string): string | null {
  if (!iconKey) return null;
  const parts = iconKey.split("::");
  if (parts.length !== 2) return null;
  const [ns, name] = parts;

  if (["sap","plc","scada","industrial","generic","security","hardware","patterns"].includes(ns)) {
    const filename = name.toLowerCase().replace(/ /g, "_").replace(/-/g, "_") + ".svg";
    return `/icons/${ns}/${filename}`;
  }

  if (ns === "cisco") {
    const filename = `Design_38_${name}.svg`;
    return `/icons/cisco/SAFE Icons Library/Design Icons (purple) .33x.38/SVG/${filename}`;
  }

  if (ns === "aws") {
    const cleanName = name.replace(/ /g, "-");
    return `/icons/aws/Icon-package_04302026/Architecture-Service-Icons_04302026/Arch_Compute/64/Arch_${cleanName}_64.svg`;
  }

  if (ns === "azure") {
    return null;
  }

  return null;
}

const NS_COLORS: Record<string, string> = {
  aws: "#FF9900",
  cisco: "#00BCEB",
  azure: "#0078D4",
  sap: "#0070F2",
  plc: "#CC0000",
  scada: "#F15A22",
  industrial: "#00695C",
  generic: "#37474F",
  security: "#E2000F",
  hardware: "#007DB8",
  patterns: "#1A237E",
};

export default function IconNode({ data }: { data: any }) {
  const [imgError, setImgError] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const iconUrl = getIconUrl(data.icon || "");
  const ns = (data.icon || "").split("::")[0];
  const color = NS_COLORS[ns] || "#6B7280";

  return (
    <div
      style={{
        background: "#111827",
        border: `1.5px solid ${color}40`,
        borderTop: `3px solid ${color}`,
        borderRadius: "10px",
        padding: "10px 12px",
        minWidth: "130px",
        maxWidth: "170px",
        cursor: "pointer",
        position: "relative",
      }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: color, width: 8, height: 8, border: "none" }}
      />

      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        {iconUrl && !imgError ? (
          <img
            src={iconUrl}
            alt={data.label}
            width={32}
            height={32}
            style={{ flexShrink: 0, borderRadius: "4px" }}
            onError={() => setImgError(true)}
          />
        ) : (
          <div style={{
            width: 32, height: 32, borderRadius: "6px",
            background: `${color}30`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "14px", fontWeight: 700, color,
            flexShrink: 0,
          }}>
            {(data.label || "?")[0]}
          </div>
        )}
        <div style={{ minWidth: 0 }}>
          <div style={{
            fontSize: "11px", fontWeight: 600, color: "#fff",
            lineHeight: 1.3, wordBreak: "break-word",
          }}>
            {data.label}
          </div>
          <div style={{ fontSize: "9px", color, marginTop: "2px", textTransform: "uppercase", letterSpacing: "0.4px" }}>
            {ns}
          </div>
        </div>
      </div>

      {showTooltip && data.description && (
        <div style={{
          position: "absolute",
          bottom: "110%",
          left: "50%",
          transform: "translateX(-50%)",
          background: "#0f0f1a",
          border: `1px solid ${color}40`,
          borderRadius: "8px",
          padding: "8px 10px",
          width: "220px",
          fontSize: "10px",
          color: "#9CA3AF",
          zIndex: 1000,
          pointerEvents: "none",
          lineHeight: 1.5,
        }}>
          <div style={{ color: "#fff", fontWeight: 600, marginBottom: "4px" }}>{data.label}</div>
          {data.description}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: color, width: 8, height: 8, border: "none" }}
      />
    </div>
  );
}
