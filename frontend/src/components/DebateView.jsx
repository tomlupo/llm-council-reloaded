import React, { useState } from 'react';

export default function DebateView({ data }) {
  const [activeTab, setActiveTab] = useState(0);

  if (!data) return null;

  const { opening, rebuttals, evaluation, verdict } = data;

  return (
    <div className="debate-view">
      {/* Opening Statements */}
      {opening && opening.length > 0 && (
        <section className="debate-section">
          <h3>Opening Statements</h3>
          <div className="model-tabs">
            {opening.map((r, i) => (
              <button
                key={i}
                className={`tab ${activeTab === i ? 'active' : ''}`}
                onClick={() => setActiveTab(i)}
              >
                {r.model}
              </button>
            ))}
          </div>
          <div className="tab-content">
            {opening[activeTab] && (
              <div className="model-response">
                {opening[activeTab].error ? (
                  <p className="error">{opening[activeTab].error}</p>
                ) : (
                  <div className="response-text">{opening[activeTab].response}</div>
                )}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Rebuttal Rounds */}
      {rebuttals && rebuttals.map((round, ri) => (
        <RoundSection key={ri} round={round} roundNum={ri + 1} />
      ))}

      {/* Peer Evaluation */}
      {evaluation && evaluation.length > 0 && (
        <section className="debate-section">
          <h3>Peer Evaluation</h3>
          <div className="evaluation-list">
            {evaluation.map((ev, i) => (
              <div key={i} className="evaluation-item">
                <strong>{ev.model}</strong>
                <div className="response-text">{ev.evaluation}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Chairman Verdict */}
      {verdict && (
        <section className="debate-section verdict">
          <h3>Chairman Verdict ({verdict.model})</h3>
          <div className="response-text">{verdict.response}</div>
        </section>
      )}
    </div>
  );
}

function RoundSection({ round, roundNum }) {
  const [tab, setTab] = useState(0);

  return (
    <section className="debate-section">
      <h3>Rebuttal Round {roundNum}</h3>
      <div className="model-tabs">
        {round.map((r, i) => (
          <button
            key={i}
            className={`tab ${tab === i ? 'active' : ''}`}
            onClick={() => setTab(i)}
          >
            {r.model}
          </button>
        ))}
      </div>
      <div className="tab-content">
        {round[tab] && !round[tab].error && (
          <div className="response-text">{round[tab].response}</div>
        )}
      </div>
    </section>
  );
}
