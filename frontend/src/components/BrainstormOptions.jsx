import React from 'react';

const STYLES = [
  { id: 'wild', label: 'Wild', description: 'Creative and unconventional' },
  { id: 'practical', label: 'Practical', description: 'Feasible and implementable' },
  { id: 'balanced', label: 'Balanced', description: 'Mix of creative and practical' },
];

export default function BrainstormOptions({ config, onConfigChange }) {
  const style = config?.style || 'balanced';
  const rounds = config?.rounds || 2;

  return (
    <div className="brainstorm-options">
      <div className="style-selector">
        {STYLES.map((s) => (
          <label key={s.id} className="style-option" title={s.description}>
            <input
              type="radio"
              name="brainstormStyle"
              value={s.id}
              checked={style === s.id}
              onChange={() => onConfigChange({ ...config, style: s.id })}
            />
            <span>{s.label}</span>
          </label>
        ))}
      </div>
      <div className="rounds-selector">
        <label>
          Rounds:
          <select
            value={rounds}
            onChange={(e) => onConfigChange({ ...config, rounds: Number(e.target.value) })}
          >
            {[1, 2, 3, 4].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}
