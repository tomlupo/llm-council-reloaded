import React from 'react';
import IdeaCard from './IdeaCard';

export default function BrainstormView({ data }) {
  if (!data) return null;

  const { style, rounds, synthesis } = data;

  return (
    <div className="brainstorm-view">
      <div className="brainstorm-meta">
        <span className="style-badge">{style}</span>
      </div>

      {/* Rounds */}
      {rounds && rounds.map((rnd, ri) => (
        <section key={ri} className="brainstorm-round">
          <h3>
            {rnd.type === 'initial'
              ? 'Round 1: Initial Ideas'
              : `Round ${rnd.round_num}: Cross-Pollination`}
          </h3>
          <div className="round-models">
            {rnd.responses && rnd.responses.map((entry, ei) => (
              <div key={ei} className="model-ideas">
                <h4>
                  {entry.model}
                  {entry.parsed_ideas && (
                    <span className="idea-count"> ({entry.parsed_ideas.length} ideas)</span>
                  )}
                </h4>
                {entry.error ? (
                  <p className="error">{entry.error}</p>
                ) : entry.parsed_ideas ? (
                  <div className="ideas-grid">
                    {entry.parsed_ideas.map((idea, ii) => (
                      <IdeaCard
                        key={ii}
                        idea={idea}
                        model={entry.model}
                        index={ii + 1}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="response-text">{entry.response}</div>
                )}
              </div>
            ))}
          </div>
        </section>
      ))}

      {/* Synthesis */}
      {synthesis && (
        <section className="brainstorm-section synthesis">
          <h3>Synthesis (Chairman: {synthesis.model})</h3>
          <div className="response-text">{synthesis.response}</div>
        </section>
      )}
    </div>
  );
}
