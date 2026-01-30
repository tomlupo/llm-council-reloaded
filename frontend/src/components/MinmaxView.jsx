import React from 'react';
import ScoreMatrix from './ScoreMatrix';

export default function MinmaxView({ data, config }) {
  if (!data) return null;

  const {
    analyses,
    aggregated_mins,
    recommendation_counts,
    chairman_recommendation,
  } = data;
  const options = config?.options || [];
  const criteria = config?.criteria || [];

  return (
    <div className="minmax-view decide-view">
      {/* Per-model minimax analyses (worst-case scores) */}
      {analyses &&
        analyses.map((analysis, i) => (
          <section key={i} className="decide-section">
            <h3>{analysis.model} — Worst-case analysis</h3>
            <ScoreMatrix
              scores={analysis.worst_case_scores}
              options={options}
              criteria={criteria}
            />
            {Object.keys(analysis.min_per_option || {}).length > 0 && (
              <p className="min-per-option">
                <strong>Min per option:</strong>{' '}
                {options
                  .map((opt) => `${opt}: ${analysis.min_per_option[opt] ?? '—'}`)
                  .join(', ')}
              </p>
            )}
            {analysis.recommendation && (
              <p className="recommendation">
                <strong>Recommends (minimax):</strong> {analysis.recommendation}
              </p>
            )}
            {analysis.reasoning && (
              <p className="reasoning">{analysis.reasoning}</p>
            )}
          </section>
        ))}

      {/* Aggregated minimum scores */}
      {aggregated_mins && (
        <section className="decide-section aggregated">
          <h3>Aggregated minimum scores (avg of worst-case)</h3>
          <table>
            <thead>
              <tr>
                <th>Option</th>
                <th>Avg min score</th>
                <th>Recommendations</th>
              </tr>
            </thead>
            <tbody>
              {options.map((opt) => (
                <tr key={opt}>
                  <td>{opt}</td>
                  <td>{(aggregated_mins[opt] ?? 0).toFixed(1)}</td>
                  <td>
                    {recommendation_counts?.[opt] || 0}/{analyses?.length || 0}{' '}
                    models
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* Chairman recommendation */}
      {chairman_recommendation && (
        <section className="decide-section verdict">
          <h3>Chairman recommendation ({chairman_recommendation.model})</h3>
          <div className="response-text">{chairman_recommendation.response}</div>
        </section>
      )}
    </div>
  );
}
