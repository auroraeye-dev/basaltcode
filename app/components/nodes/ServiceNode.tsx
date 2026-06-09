import { Handle, Position } from "@xyflow/react";

const SERVICE_COLORS: Record<string, string> = {
  // AWS
  "AWS WAF": "#DD344C",
  "AWS IoT Greengrass": "#1A9C3E",
  "AWS IoT Core": "#1A9C3E",
  "CloudFront": "#8C4FFF",
  "AWS Shield": "#DD344C",
  "EC2": "#FF9900",
  "EC2 Auto Scaling": "#FF9900",
  "EKS": "#FF9900",
  "Lambda": "#FF9900",
  "Aurora PostgreSQL": "#3F48CC",
  "Aurora MySQL": "#3F48CC",
  "RDS": "#3F48CC",
  "DynamoDB": "#3F48CC",
  "Timestream": "#3F48CC",
  "ElastiCache Redis": "#3F48CC",
  "KMS": "#DD344C",
  "GuardDuty": "#DD344C",
  "CloudTrail": "#DD344C",
  "Secrets Manager": "#DD344C",
  "Macie": "#DD344C",
  "Security Hub": "#DD344C",
  "VPC": "#8C4FFF",
  "Private Subnets": "#8C4FFF",
  "NAT Gateway": "#8C4FFF",
  "Direct Connect": "#8C4FFF",
  "Transit Gateway": "#8C4FFF",
  "PrivateLink": "#8C4FFF",
  "CloudWatch": "#FF4F8B",
  "AWS IoT Analytics": "#FF4F8B",
  "Application Load Balancer": "#FF9900",
  "Network Load Balancer": "#FF9900",
  "Route 53": "#8C4FFF",
  // Cisco / On-prem
  "Cisco Router": "#00BCEB",
  "Cisco Switch": "#00BCEB",
  "Cisco Firewall": "#00BCEB",
  "Cisco ASA": "#00BCEB",
  "Palo Alto NGFW": "#FA582D",
  "Fortinet": "#EE3124",
  "PLC": "#5C6BC0",
  "SCADA Server": "#5C6BC0",
  "HMI": "#5C6BC0",
  "Historian": "#5C6BC0",
  "DCS": "#5C6BC0",
};

const SERVICE_ICONS: Record<string, string> = {
  "AWS WAF": "🛡",
  "CloudFront": "🌐",
  "EC2": "🖥",
  "EC2 Auto Scaling": "🖥",
  "EKS": "⚙",
  "Lambda": "λ",
  "Aurora PostgreSQL": "🗄",
  "Aurora MySQL": "🗄",
  "RDS": "🗄",
  "DynamoDB": "🗄",
  "Timestream": "📊",
  "ElastiCache Redis": "⚡",
  "KMS": "🔑",
  "GuardDuty": "👁",
  "CloudTrail": "📋",
  "CloudWatch": "📡",
  "VPC": "☁",
  "Direct Connect": "🔌",
  "Cisco Router": "🔀",
  "Cisco Switch": "🔀",
  "Cisco Firewall": "🔥",
  "PLC": "⚙",
  "SCADA Server": "🖥",
  "HMI": "🖥",
  "Historian": "🗄",
  "AWS IoT Greengrass": "🌿",
  "AWS IoT Core": "📡",
};

export default function ServiceNode({ data }: { data: any }) {
  const color = SERVICE_COLORS[data.label] || "#6B7280";
  const icon = SERVICE_ICONS[data.label] || "◆";

  return (
    <div
      style={{
        background: "#1a1a2e",
        border: `1.5px solid ${color}40`,
        borderTop: `3px solid ${color}`,
        borderRadius: "8px",
        padding: "10px 14px",
        minWidth: "140px",
        maxWidth: "180px",
        cursor: "grab",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: color, width: 8, height: 8 }} />
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span style={{ fontSize: "18px" }}>{icon}</span>
        <div>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#fff", lineHeight: 1.3 }}>
            {data.label}
          </div>
          {data.tier && (
            <div style={{ fontSize: "9px", color: color, marginTop: "2px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              {data.tier}
            </div>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} style={{ background: color, width: 8, height: 8 }} />
    </div>
  );
}
