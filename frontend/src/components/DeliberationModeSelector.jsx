import React from 'react';

const MODES = [
  {
    id: 'ask',
    label: 'Ask',
    description: 'Each model answers independently; peer review and chairman synthesis produce a final answer.',
  },
  {
    id: 'debate',
    label: 'Debate',
    description: 'Structured multi-round debate: opening statements, rebuttals, then chairman verdict.',
  },
  {
    id: 'decide',
    label: 'Decide',
    description: 'Models score and rank your options; chairman recommends based on analyses.',
  },
  {
    id: 'minmax',
    label: 'Minmax',
    description: 'Worst-case analysis: each option is scored by its minimum outcome across criteria; best worst-case wins.',
  },
  {
    id: 'brainstorm',
    label: 'Brainstorm',
    description: 'Models propose ideas in rounds; chairman synthesizes into a consolidated list.',
  },
];

export default function DeliberationModeSelector({ mode, onChange }) {
  const selectedMode = MODES.find((m) => m.id === mode);

  return (
    <div className="mode-selector-wrap">
      <div className="mode-selector">
        {MODES.map((m) => (
          <button
            key={m.id}
            className={`mode-tab ${mode === m.id ? 'active' : ''}`}
            onClick={() => onChange(m.id)}
            title={m.description}
            type="button"
          >
            {m.label}
          </button>
        ))}
      </div>
      {selectedMode && (
        <p className="mode-description" title={selectedMode.description}>
          {selectedMode.description}
        </p>
      )}
    </div>
  );
}
