import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Streamdown } from 'streamdown';
import DeliberationModeSelector from './DeliberationModeSelector';
import ExecutionModeToggle from './ExecutionModeToggle';
import DecideInputForm from './DecideInputForm';
import BrainstormOptions from './BrainstormOptions';
import DebateOptions from './DebateOptions';
import DebateView from './DebateView';
import DecideView from './DecideView';
import MinmaxView from './MinmaxView';
import BrainstormView from './BrainstormView';
import { createConversation, sendMessageStream } from '../api';

function MarkdownContent({ content, className }) {
  if (content == null || content === '') return null;
  const text = typeof content === 'string' ? content : String(content);
  return (
    <div className={className}>
      <Streamdown>{text}</Streamdown>
    </div>
  );
}

export default function ChatInterface({
  deliberationMode,
  onDeliberationModeChange,
  executionMode,
  onExecutionModeChange,
  modeConfig,
  onModeConfigChange,
}) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState('');
  const [streamProgress, setStreamProgress] = useState([]);
  const [streamStageState, setStreamStageState] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const abortRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamProgress]);

  const handleSend = useCallback(async () => {
    const content = input.trim();
    if (!content || isStreaming) return;

    // Validate decide/minmax mode has options
    if (deliberationMode === 'decide' || deliberationMode === 'minmax') {
      const opts = modeConfig?.options || [];
      if (opts.length < 2) {
        alert(
          deliberationMode === 'minmax'
            ? 'Minmax mode requires at least 2 options'
            : 'Decide mode requires at least 2 options'
        );
        return;
      }
    }

    setInput('');
    setIsStreaming(true);
    setStreamStatus('Starting...');
    setStreamProgress([]);
    setStreamStageState(null);

    // Add user message
    setMessages((prev) => [...prev, { role: 'user', content }]);

    // Create conversation if needed
    let convId = conversationId;
    if (!convId) {
      const { id } = await createConversation();
      convId = id;
      setConversationId(id);
    }

    // Collect streaming data
    const collected = { events: [], modeData: null };

    const { abort } = sendMessageStream(
      convId,
      {
        content,
        executionMode,
        deliberationMode: deliberationMode,
        modeConfig: modeConfig,
      },
      // onEvent
      (eventName, data) => {
        collected.events.push({ event: eventName, data });
        setStreamStatus(formatEventStatus(eventName, data));

        // Track progress events
        if (eventName.includes('_progress')) {
          setStreamProgress((prev) => [...prev, { event: eventName, ...data }]);
        }

        // Track stage state for Ask mode (timeline + Responses / Peer review labels)
        setStreamStageState((prev) => {
          const next = { ...prev };
          if (eventName === 'stage1_start') next.stage = 1;
          if (eventName === 'stage1_init') {
            next.stage1Models = data.models || [];
            next.stage1Done = [];
          }
          if (eventName === 'stage1_progress' && data.model) {
            next.stage1Done = [...(next.stage1Done || []), data.model];
          }
          if (eventName === 'stage1_complete') next.stage1Complete = true;
          if (eventName === 'stage2_start') {
            next.stage = 2;
            next.stage2Reviewed = 0;
            next.stage2Total = next.stage1Models?.length ?? 0;
          }
          if (eventName === 'stage2_progress') {
            next.stage2Reviewed = data.reviewed_count ?? 0;
            next.stage2Total = data.total ?? next.stage2Total;
          }
          if (eventName === 'stage2_complete') next.stage2Complete = true;
          if (eventName === 'stage3_start') next.stage = 3;
          if (eventName === 'stage3_complete') next.stage3Complete = true;
          return next;
        });

        // Capture mode-specific data from completion events
        if (eventName === 'debate_complete' && data.debate) {
          collected.modeData = { type: 'debate', data: data.debate, config: data.metadata };
        } else if (eventName === 'decide_complete' && data.decision) {
          collected.modeData = { type: 'decide', data: data.decision, config: data.metadata };
        } else if (eventName === 'minmax_complete' && data.minmax) {
          collected.modeData = { type: 'minmax', data: data.minmax, config: data.metadata };
        } else if (eventName === 'brainstorm_complete' && data.brainstorm) {
          collected.modeData = { type: 'brainstorm', data: data.brainstorm, config: data.metadata };
        } else if (eventName === 'ask_complete') {
          collected.modeData = {
            type: 'ask',
            data: { stage1: data.stage1, stage2: data.stage2, stage3: data.stage3 },
          };
        }
      },
      // onDone
      () => {
        setIsStreaming(false);
        setStreamStatus('');
        setStreamStageState(null);

        const msg = {
          role: 'assistant',
          content: collected.modeData?.data?.stage3 ||
            collected.events.find((e) => e.data?.content)?.data?.content || '',
          modeData: collected.modeData,
          deliberationMode,
        };
        setMessages((prev) => [...prev, msg]);
        setStreamProgress([]);
      },
      // onError
      (err) => {
        setIsStreaming(false);
        setStreamStatus('');
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `Error: ${err.message}`, error: true },
        ]);
      }
    );

    abortRef.current = abort;
  }, [input, isStreaming, conversationId, deliberationMode, executionMode, modeConfig]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    setStreamProgress([]);
  };

  return (
    <div className="chat-interface">
      {/* Mode selector */}
      <div className="chat-controls">
        <DeliberationModeSelector mode={deliberationMode} onChange={onDeliberationModeChange} />

        {/* Show execution mode toggle only for Ask mode */}
        {deliberationMode === 'ask' && (
          <ExecutionModeToggle mode={executionMode} onChange={onExecutionModeChange} />
        )}

        {/* Mode-specific options */}
        {deliberationMode === 'debate' && (
          <DebateOptions config={modeConfig} onConfigChange={onModeConfigChange} />
        )}
        {deliberationMode === 'decide' && (
          <DecideInputForm onConfigChange={onModeConfigChange} />
        )}
        {deliberationMode === 'minmax' && (
          <DecideInputForm onConfigChange={onModeConfigChange} />
        )}
        {deliberationMode === 'brainstorm' && (
          <BrainstormOptions config={modeConfig} onConfigChange={onModeConfigChange} />
        )}
      </div>

      {/* Messages */}
      <div className="messages-container">
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {/* Streaming indicator */}
        {isStreaming && (
          <div className="streaming-indicator">
            <div className="streaming-indicator-row">
              <div className="spinner" />
              <span>{streamStatus}</span>
            </div>
            {streamStageState && deliberationMode === 'ask' && (
              <div className="stream-stage-detail">
                <div className="stage-timeline">
                  <span className={streamStageState.stage >= 1 ? 'done' : ''}>
                    Stage 1 {streamStageState.stage1Complete ? '✓' : '…'}
                  </span>
                  <span> → </span>
                  <span className={streamStageState.stage >= 2 ? 'done' : ''}>
                    Stage 2 {streamStageState.stage2Complete ? '✓' : '…'}
                  </span>
                  <span> → </span>
                  <span className={streamStageState.stage >= 3 ? 'done' : ''}>
                    Stage 3 {streamStageState.stage3Complete ? '✓' : '…'}
                  </span>
                </div>
                {streamStageState.stage1Models?.length > 0 && (
                  <div className="stage1-models">
                    Responses: {streamStageState.stage1Models.map((m) => (
                      <span key={m} className="model-status">
                        {m} {(streamStageState.stage1Done || []).includes(m) ? '✓' : '…'}
                      </span>
                    ))}
                  </div>
                )}
                {streamStageState.stage === 2 && streamStageState.stage2Total > 0 && (
                  <div className="stage2-progress">
                    Peer review: {streamStageState.stage2Reviewed ?? 0}/{streamStageState.stage2Total} models
                    {streamStageState.stage2Total > 1 && (
                      <span className="stage2-hint"> (typically 1–2 min)</span>
                    )}
                  </div>
                )}
              </div>
            )}
            {streamProgress.length > 0 && (
              <div className="progress-items">
                {streamProgress.slice(-5).map((p, i) => (
                  <div key={i} className="progress-item">
                    {p.model && <span className="model-badge">{p.model}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="input-area">
        <button className="new-chat-btn" onClick={handleNewConversation} title="New conversation">
          +
        </button>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={getPlaceholder(deliberationMode)}
          disabled={isStreaming}
          rows={2}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={isStreaming || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}

/** Normalize stored mode_data (from API) to UI shape { type, data, config }. */
function normalizeModeData(raw) {
  if (!raw || (raw.type && raw.data)) return raw;
  if (raw.ask_complete && (raw.ask_complete.stage1 || raw.ask_complete.stage3)) {
    return { type: 'ask', data: raw.ask_complete };
  }
  if (raw.debate_complete?.debate) {
    return { type: 'debate', data: raw.debate_complete.debate, config: raw.debate_complete.metadata };
  }
  if (raw.decide_complete?.decision) {
    return { type: 'decide', data: raw.decide_complete.decision, config: raw.decide_complete.metadata };
  }
  if (raw.minmax_complete?.minmax) {
    return { type: 'minmax', data: raw.minmax_complete.minmax, config: raw.minmax_complete.metadata };
  }
  if (raw.brainstorm_complete?.brainstorm) {
    return { type: 'brainstorm', data: raw.brainstorm_complete.brainstorm, config: raw.brainstorm_complete.metadata };
  }
  return null;
}

function MessageBubble({ message }) {
  const { role, content, modeData: rawModeData, mode_data: rawModeDataSnake, error } = message;
  const modeData = normalizeModeData(rawModeData || rawModeDataSnake);

  return (
    <div className={`message ${role} ${error ? 'error' : ''}`}>
      <div className="message-header">{role === 'user' ? 'You' : 'Council'}</div>

      {/* Render mode-specific view for assistant messages */}
      {role === 'assistant' && modeData ? (
        <div className="mode-view">
          {modeData.type === 'debate' && <DebateView data={modeData.data} />}
          {modeData.type === 'decide' && (
            <DecideView data={modeData.data} config={modeData.config?.decide_config} />
          )}
          {modeData.type === 'minmax' && (
            <MinmaxView data={modeData.data} config={modeData.config?.minmax_config} />
          )}
          {modeData.type === 'brainstorm' && <BrainstormView data={modeData.data} />}
          {modeData.type === 'ask' && modeData.data?.stage1 && (
            <AskView data={modeData.data} />
          )}
        </div>
      ) : (
        <div className="message-content">
          <MarkdownContent content={content} className="message-content-markdown" />
        </div>
      )}
    </div>
  );
}

function AskView({ data }) {
  const [activeModel, setActiveModel] = useState(0);
  const { stage1, stage3 } = data;

  return (
    <div className="ask-view">
      {stage1 && (
        <section>
          <h3>Individual Responses</h3>
          <div className="model-tabs">
            {stage1.map((r, i) => (
              <button
                key={i}
                className={`tab ${activeModel === i ? 'active' : ''}`}
                onClick={() => setActiveModel(i)}
              >
                {r.model}
              </button>
            ))}
          </div>
          <div className="tab-content">
            {stage1[activeModel] && (
              <div className="response-text">
                {stage1[activeModel].error ? (
                  stage1[activeModel].error
                ) : (
                  <MarkdownContent content={stage1[activeModel].response} className="response-text-markdown" />
                )}
              </div>
            )}
          </div>
        </section>
      )}
      {stage3 && (
        <section className="synthesis">
          <h3>Chairman Synthesis</h3>
          <div className="response-text">
            <MarkdownContent content={stage3} className="response-text-markdown" />
          </div>
        </section>
      )}
    </div>
  );
}

function formatEventStatus(event, data) {
  const statusMap = {
    stage1_start: 'Gathering independent responses...',
    stage1_init: data.models?.length
      ? `Gathering responses from: ${data.models.join(', ')}...`
      : 'Gathering independent responses...',
    stage1_progress: `${data.model || ''} responded`,
    stage2_start: 'Peer review in progress...',
    stage2_progress: data.total
      ? `Peer review: ${data.reviewed_count ?? 0}/${data.total} models`
      : 'Peer review in progress...',
    stage3_start: 'Chairman synthesizing...',
    debate_start: 'Starting debate...',
    debate_opening_init: 'Opening statements...',
    debate_opening_progress: `${data.model || ''} opening...`,
    debate_rebuttal_start: `Rebuttal round ${data.round || ''}...`,
    debate_rebuttal_progress: `${data.model || ''} rebuttal...`,
    debate_evaluation_start: 'Peer evaluation...',
    debate_verdict_start: 'Chairman deliberating verdict...',
    decide_start: 'Starting decision analysis...',
    decide_analysis_init: 'Models analyzing options...',
    decide_analysis_progress: `${data.model || ''} analyzing...`,
    decide_evaluation_start: 'Peer evaluation...',
    decide_recommendation_start: 'Chairman forming recommendation...',
    minmax_start: 'Starting minimax analysis...',
    minmax_analysis_init: 'Models evaluating worst-case...',
    minmax_analysis_progress: `${data.model || ''} minimax...`,
    minmax_recommendation_start: 'Chairman forming minimax recommendation...',
    brainstorm_start: 'Starting brainstorm...',
    brainstorm_round_start: `Round ${data.round || ''}: ${data.type === 'initial' ? 'Initial ideas' : 'Cross-pollination'}...`,
    brainstorm_round_progress: `${data.model || ''} ideating...`,
    brainstorm_synthesis_start: 'Chairman synthesizing ideas...',
  };
  return statusMap[event] || event.replace(/_/g, ' ');
}

function getPlaceholder(mode) {
  const placeholders = {
    ask: 'Ask the council anything...',
    debate: 'Enter a debate topic...',
    decide: 'Describe the decision to make...',
    minmax: 'Describe the decision (options below)...',
    brainstorm: 'Enter a brainstorming topic...',
  };
  return placeholders[mode] || 'Type a message...';
}
