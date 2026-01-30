import React from 'react';

export default function DebateOptions({ config, onConfigChange }) {
  const rounds = config?.rounds || 2;

  return (
    <div className="debate-options">
      <div className="rounds-selector">
        <label>
          Rounds:
          <select
            value={rounds}
            onChange={(e) => onConfigChange({ ...config, rounds: Number(e.target.value) })}
          >
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}
