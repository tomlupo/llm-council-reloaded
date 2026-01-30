import React from 'react';

export default function ScoreMatrix({ scores, options, criteria }) {
  if (!scores || !options || !criteria) return null;

  return (
    <div className="score-matrix">
      <table>
        <thead>
          <tr>
            <th>Option</th>
            {criteria.map((c) => (
              <th key={c}>{c}</th>
            ))}
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          {options.map((opt) => {
            const optScores = scores[opt] || {};
            const total = criteria.reduce((sum, c) => sum + (optScores[c] || 0), 0);
            return (
              <tr key={opt}>
                <td className="option-name">{opt}</td>
                {criteria.map((c) => (
                  <td key={c} className="score-cell">
                    {optScores[c] ?? '-'}
                  </td>
                ))}
                <td className="total-cell">{total}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
