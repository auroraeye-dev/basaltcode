"use client";
import { Handle, Position } from "@xyflow/react";
import { useState, memo } from "react";

let REGISTRY: Record<string, string> | null = null;
let registryLoading = false;
const listeners: (() => void)[] = [];

function loadRegistry() {
  if (REGISTRY || registryLoading) return;
  registryLoading = true;
  fetch("/icons/registry.json")
    .then((r) => r.json())
    .then((data) => { REGISTRY = data; listeners.forEach((fn) => fn()); })
    .catch(() => { REGISTRY = {}; });
}

function getIconUrl(iconKey: string): string | null {
  if (!iconKey) return null;
  if (REGISTRY && REGISTRY[iconKey]) return REGISTRY[iconKey];

  const parts = iconKey.split("::");
  if (parts.length !== 2) return null;
  const [ns, name] = parts;

  if (["sap","plc","scada","industrial","generic","security","hardware","patterns"].includes(ns)) {
    const filename = name.toLowerCase().replace(/ /g, "_").replace(/-/g, "_") + ".svg";
    return `/icons/${ns}/${filename}`;
  }
  if (ns === "cisco") {
    return `/icons/cisco/SAFE Icons Library/Design Icons (purple) .33x.38/SVG/Design_38_${name}.svg`;
  }
  return null;
}

const NS_LABEL: Record<string, string> = {
  aws: "AWS", cisco: "Cisco", azure: "Azure", sap: "SAP", plc: "PLC",
  scada: "SCADA", industrial: "Industrial", generic: "Generic",
  security: "Security", hardware: "Hardware", patterns: "Pattern",
};

function IconNode({ data, selected }: { data: any; selected?: boolean }) {
  const [, force] = useState(0);
  const [imgError, setImgError] = useState(false);
  const [hover, setHover] = useState(false);

  if (!REGISTRY) {
    loadRegistry();
    listeners.push(() => force((n) => n + 1));
  }

  const accent = data.accent || "#8FB4E8";
  const iconUrl = getIconUrl(data.icon || "");
  const ns = (data.icon || "").split("::")[0];

  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        width: 180,
        background: "#0F1218",
        borderWidth: "1px",
        borderStyle: "solid",
        borderColor: selected ? accent : "#262B36",
        borderTopWidth: "2.5px",
        borderTopColor: accent,
        borderRadius: "10px",
        padding: "11px 12px",
        boxShadow: selected ? `0 0 0 1px ${accent}, 0 4px 20px rgba(0,0,0,0.5)` : hover ? `0 4px 16px rgba(0,0,0,0.45)` : "0 2px 8px rgba(0,0,0,0.3)",
        transition: "box-shadow 0.15s, border-color 0.15s",
        position: "relative",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: accent, width: 7, height: 7, border: "none" }} />
      <Handle type="target" position={Position.Left} style={{ background: accent, width: 7, height: 7, border: "none" }} />

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 8, flexShrink: 0,
          background: imgError || !iconUrl ? `${accent}22` : "#fff",
          display: "flex", alignItems: "center", justifyContent: "center",
          overflow: "hidden",
        }}>
          {iconUrl && !imgError ? (
            <img src={iconUrl} alt={data.label} width={30} height={30} onError={() => setImgError(true)} />
          ) : (
            <span style={{ fontSize: 15, fontWeight: 700, color: accent }}>{(data.label || "?")[0]}</span>
          )}
        </div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontSize: 11.5, fontWeight: 600, color: "#EAF0F8", lineHeight: 1.25 }}>{data.label}</div>
          <div style={{ fontSize: 8.5, color: accent, marginTop: 3, textTransform: "uppercase", letterSpacing: "0.5px", fontWeight: 600 }}>
            {NS_LABEL[ns] || ns}
          </div>
        </div>
      </div>

      {hover && data.description && (
        <div style={{
          position: "absolute", bottom: "112%", left: "50%", transform: "translateX(-50%)",
          background: "#0B0D12", border: `1px solid ${accent}55`, borderRadius: 8,
          padding: "9px 11px", width: 230, fontSize: 10, color: "#A8B2C2",
          zIndex: 1000, pointerEvents: "none", lineHeight: 1.55,
          boxShadow: "0 8px 24px rgba(0,0,0,0.6)",
        }}>
          <div style={{ color: "#EAF0F8", fontWeight: 600, marginBottom: 4 }}>{data.label}</div>
          {data.description}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} style={{ background: accent, width: 7, height: 7, border: "none" }} />
      <Handle type="source" position={Position.Right} style={{ background: accent, width: 7, height: 7, border: "none" }} />
    </div>
  );
}

export default memo(IconNode);
