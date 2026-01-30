import React, { useState, useCallback } from 'react';
import ChatInterface from './components/ChatInterface';
import Settings from './components/Settings';

export default function App() {
  const [view, setView] = useState('chat'); // 'chat' | 'settings'
  const [deliberationMode, setDeliberationMode] = useState('ask');
  const [executionMode, setExecutionMode] = useState('full');
  const [modeConfig, setModeConfig] = useState(null);

  const handleModeChange = useCallback((mode) => {
    setDeliberationMode(mode);
    setModeConfig(null);
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1 onClick={() => setView('chat')}>LLM Council Plus</h1>
        <nav>
          <button
            className={view === 'chat' ? 'active' : ''}
            onClick={() => setView('chat')}
          >
            Council
          </button>
          <button
            className={view === 'settings' ? 'active' : ''}
            onClick={() => setView('settings')}
          >
            Settings
          </button>
        </nav>
      </header>

      <main>
        {view === 'chat' ? (
          <ChatInterface
            deliberationMode={deliberationMode}
            onDeliberationModeChange={handleModeChange}
            executionMode={executionMode}
            onExecutionModeChange={setExecutionMode}
            modeConfig={modeConfig}
            onModeConfigChange={setModeConfig}
          />
        ) : (
          <Settings />
        )}
      </main>
    </div>
  );
}
