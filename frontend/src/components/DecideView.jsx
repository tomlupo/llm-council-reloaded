import React from 'react';
import ScoreMatrix from './ScoreMatrix';

export default function DecideView({ data, config }) {
  if (!data) return null;

  const { analyses, aggregated_scores, recommendation_counts, chairman_recommendation } = data;
  const options = config?.options || [];
  const criteria = config?.criteria || [];

  return (
    <div className="decide-view">
      {/* Per-model analyses */}
      {analyses && analyses.map((analysis, i) => (
        <section key={i} className="decide-section">
          <h3>{analysis.model} Analysis</h3>
          <ScoreMatrix
            scores={analysis.scores}
            options={options}
            criteria={criteria}
          />
          {analysis.recommendation && (
            <p className="recommendation">
              <strong>Recommends:</strong> {analysis.recommendation}
            </p>
          )}
          {analysis.reasoning && (
            <p className="reasoning">{analysis.reasoning}</p>
          )}
        </section>
      ))}

      {/* Aggregated scores */}
      {aggregated_scores && (
        <section className="decide-section aggregated">
          <h3>Aggregated Scores</h3>
          <table>
            <thead>
              <tr>
                <th>Option</th>
                <th>Avg Score</th>
                <th>Recommendations</th>
              </tr>
            </thead>
            <tbody>
              {options.map((opt) => (
                <tr key={opt}>
                  <td>{opt}</td>
                  <td>{(aggregated_scores[opt] || 0).toFixed(1)}</td>
                  <td>
                    {recommendation_counts?.[opt] || 0}/{analyses?.length || 0} models
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
          <h3>Chairman Recommendation ({chairman_recommendation.model})</h3>
          <div className="response-text">{chairman_recommendation.response}</div>
        </section>
      )}
    </div>
  );
}
