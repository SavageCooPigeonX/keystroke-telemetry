/* RegionLabel — floating brain region label above each neuron cluster */
import React from 'react';

export default function RegionLabel({ data }) {
  return (
    <div className="region-label" style={{ color: data.color, borderColor: `${data.color}44` }}>
      <span className="region-icon">{data.icon}</span>
      <span className="region-name">{data.name}</span>
      <span className="region-count">{data.count}</span>
    </div>
  );
}
