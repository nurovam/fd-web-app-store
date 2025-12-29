import type { FC } from "react";
import type { Feature } from "../types";

type Props = {
  items: Feature[];
};

const FeatureStrip: FC<Props> = ({ items }) => (
  <div className="card" style={{ padding: 18, marginTop: 18 }}>
    <div className="grid cols-4">
      {items.map((feature) => (
        <div key={feature.title} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              background: "#eef3fb",
              display: "grid",
              placeItems: "center",
              fontSize: 20
            }}
          >
            {feature.icon}
          </div>
          <div>
            <div style={{ fontWeight: 700, color: "#1b2f48" }}>{feature.title}</div>
            <div style={{ color: "#6d7f99", fontSize: 14 }}>{feature.description}</div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

export default FeatureStrip;
