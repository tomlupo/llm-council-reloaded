import React from 'react';

const MODES = [
  {
    id: 'full',
    label: 'Full Council',
    description: 'All 3 stages: individual responses, peer review, and chairman synthesis.',
  },
  {
    id: 'chat_only',
    label: 'Chat Only',
    description: 'Stage 1 only — each model responds; no peer review or synthesis.',
  },
  {
    id: 'chat_ranking',
    label: 'Chat + Ranking',
    description: 'Stage 1 and 2 — responses plus peer review and ranking; no chairman synthesis.',
  },
];

export default function ExecutionModeToggle({ mode, onChange }) {
  return (
    <div className="execution-mode-toggle">
      {MODES.map((m) => (
        <label key={m.id} className="execution-mode-option" title={m.description}>
          <input
            type="radio"
            name="executionMode"
            value={m.id}
            checked={mode === m.id}
            onChange={() => onChange(m.id)}
          />
          <span>{m.label}</span>
        </label>
      ))}
    </div>
  );
}
