import React, { useState } from 'react';

const DEFAULT_CRITERIA = ['feasibility', 'cost', 'complexity', 'maintainability'];

export default function DecideInputForm({ onConfigChange }) {
  const [options, setOptions] = useState('');
  const [criteria, setCriteria] = useState(DEFAULT_CRITERIA.join(', '));

  const handleChange = (newOptions, newCriteria) => {
    const opts = newOptions.split(',').map((s) => s.trim()).filter(Boolean);
    const crits = newCriteria.split(',').map((s) => s.trim()).filter(Boolean);
    onConfigChange({
      options: opts,
      criteria: crits.length > 0 ? crits : DEFAULT_CRITERIA,
    });
  };

  return (
    <div className="decide-input-form">
      <div className="form-group">
        <label>Options (comma-separated)</label>
        <input
          type="text"
          value={options}
          onChange={(e) => {
            setOptions(e.target.value);
            handleChange(e.target.value, criteria);
          }}
          placeholder="PostgreSQL, MongoDB, Redis"
        />
      </div>
      <div className="form-group">
        <label>Criteria (comma-separated)</label>
        <input
          type="text"
          value={criteria}
          onChange={(e) => {
            setCriteria(e.target.value);
            handleChange(options, e.target.value);
          }}
          placeholder="feasibility, cost, complexity, maintainability"
        />
      </div>
    </div>
  );
}
