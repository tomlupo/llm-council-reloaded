import React from 'react';

export default function IdeaCard({ idea, model, index }) {
  return (
    <div className="idea-card">
      <span className="idea-number">{index}.</span>
      <span className="idea-text">{idea}</span>
      {model && <span className="idea-origin">{model}</span>}
    </div>
  );
}
