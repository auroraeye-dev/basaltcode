"use client";
import { memo } from "react";

function ZoneGroup({ data }: { data: any }) {
  const theme = data.theme || { bg: "rgba(200,210,225,0.04)", border: "#6A7585", accent: "#A8B2C2" };
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: theme.bg,
        border: `1px solid ${theme.border}55`,
        borderLeft: `3px solid ${theme.border}`,
        borderRadius: "14px",
        position: "relative",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 12,
          left: 16,
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div style={{ width: 7, height: 7, borderRadius: "50%", background: theme.accent }} />
        <span
          style={{
            color: theme.accent,
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: "0.8px",
            textTransform: "uppercase",
          }}
        >
          {data.label}
        </span>
      </div>
    </div>
  );
}

export default memo(ZoneGroup);
