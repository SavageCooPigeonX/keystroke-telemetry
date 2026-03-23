/* ElectronLayer — animated dots representing live electrons */
import React from 'react';

export default function ElectronLayer({ electrons }) {
  if (!electrons || !electrons.length) return null;

  return (
    <div className="electron-layer">
      {electrons.map((e, i) => {
        const status = e.status || 'flowing';
        const colors = {
          flowing: '#00ff88',
          blocked: '#ffaa00',
          stalled: '#ff6600',
          looping: '#ff00ff',
          dead: '#ff0000',
          complete: '#00ddff',
        };
        return (
          <div
            key={e.job_id || i}
            className={`electron ${status}`}
            style={{
              background: colors[status] || '#00ff88',
              boxShadow: `0 0 8px ${colors[status] || '#00ff88'}`,
            }}
            title={`${e.job_id} — ${status}`}
          />
        );
      })}
    </div>
  );
}
