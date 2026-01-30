import React, { useState, useEffect } from 'react';
import { getSettings, updateSettings, getModelCatalog } from '../api';
import SearchableSelect from './SearchableSelect';

export default function Settings() {
  const [settings, setSettings] = useState(null);
  const [catalog, setCatalog] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    getSettings().then(setSettings).catch(() => setMessage('Failed to load settings'));
  }, []);

  useEffect(() => {
    getModelCatalog().then(setCatalog).catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    try {
      await updateSettings(settings);
      setMessage('Settings saved');
    } catch {
      setMessage('Failed to save settings');
    }
    setSaving(false);
  };

  if (!settings) return <div className="settings-loading">Loading settings...</div>;

  const updateField = (path, value) => {
    setSettings((prev) => {
      const next = JSON.parse(JSON.stringify(prev));
      const parts = path.split('.');
      let obj = next;
      for (let i = 0; i < parts.length - 1; i++) {
        obj = obj[parts[i]];
      }
      obj[parts[parts.length - 1]] = value;
      return next;
    });
  };

  return (
    <div className="settings">
      <h2>Settings</h2>

      {/* Models */}
      <section className="settings-section">
        <h3>Models</h3>
        {settings.models.map((model, i) => (
          <div key={i} className="model-config">
            <label className="model-toggle">
              <input
                type="checkbox"
                checked={model.enabled}
                onChange={(e) => updateField(`models.${i}.enabled`, e.target.checked)}
              />
            </label>
            {catalog ? (
              <select
                className="provider-select"
                value={model.provider}
                onChange={(e) => {
                  const provider = e.target.value;
                  const def = catalog.provider_defaults[provider];
                  const first = def?.models?.[0];
                  updateField(`models.${i}.provider`, provider);
                  updateField(`models.${i}.endpoint`, first?.endpoint ?? def?.endpoint ?? '');
                  updateField(`models.${i}.api_key_env`, def?.api_key_env ?? '');
                  if (first) updateField(`models.${i}.model`, first.id);
                }}
              >
                {catalog.providers.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            ) : (
              <span className="provider-badge">{model.provider}</span>
            )}
            {catalog?.provider_defaults?.[model.provider] ? (
              <SearchableSelect
                options={catalog.provider_defaults[model.provider].models}
                value={model.model}
                placeholder={`Model: ${model.model}`}
                onChange={(id, option) => {
                  updateField(`models.${i}.model`, id);
                  if (option?.endpoint) updateField(`models.${i}.endpoint`, option.endpoint);
                }}
              />
            ) : (
              <span className="model-id-fallback">{model.model}</span>
            )}
            <button
              type="button"
              className="model-remove-btn"
              onClick={() => {
                setSettings((prev) => {
                  const next = JSON.parse(JSON.stringify(prev));
                  next.models = next.models.filter((_, idx) => idx !== i);
                  return next;
                });
              }}
              title="Remove model"
            >
              Remove
            </button>
          </div>
        ))}
        {catalog && (
          <button
            type="button"
            className="add-model-btn"
            onClick={() => {
              const provider = catalog.providers[0];
              const def = catalog.provider_defaults[provider];
              const first = def.models[0];
              setSettings((prev) => {
                const next = JSON.parse(JSON.stringify(prev));
                next.models.push({
                  name: first?.id?.split(/[-.]/)[0] || provider,
                  provider,
                  model: first?.id ?? '',
                  endpoint: first?.endpoint ?? def.endpoint,
                  api_key_env: def.api_key_env,
                  enabled: true,
                });
                return next;
              });
            }}
          >
            Add model
          </button>
        )}
      </section>

      {/* Council Config */}
      <section className="settings-section">
        <h3>Council</h3>
        <div className="form-group">
          <label>Chairman Strategy</label>
          <select
            value={settings.council.chairman_strategy}
            onChange={(e) => updateField('council.chairman_strategy', e.target.value)}
          >
            <option value="rotating">Rotating</option>
            <option value="fixed">Fixed</option>
          </select>
        </div>
        {settings.council.chairman_strategy === 'fixed' && (
          <div className="form-group">
            <label>Fixed Chairman Model</label>
            <select
              value={settings.council.chairman_fixed_model || ''}
              onChange={(e) => updateField('council.chairman_fixed_model', e.target.value || null)}
            >
              <option value="">Select model</option>
              {settings.models.map((m) => (
                <option key={m.name} value={m.name}>{m.name}</option>
              ))}
            </select>
          </div>
        )}
      </section>

      {/* Deliberation Mode Defaults */}
      <section className="settings-section">
        <h3>Deliberation Modes</h3>

        <div className="form-group">
          <label>Default Mode</label>
          <select
            value={settings.default_deliberation_mode}
            onChange={(e) => updateField('default_deliberation_mode', e.target.value)}
          >
            <option value="ask">Ask</option>
            <option value="debate">Debate</option>
            <option value="decide">Decide</option>
            <option value="brainstorm">Brainstorm</option>
          </select>
        </div>

        <h4>Debate Defaults</h4>
        <div className="form-group">
          <label>Default Rounds</label>
          <input
            type="number"
            min={1}
            max={10}
            value={settings.debate_defaults.rounds}
            onChange={(e) => updateField('debate_defaults.rounds', Number(e.target.value))}
          />
        </div>

        <h4>Decide Defaults</h4>
        <div className="form-group">
          <label>Default Criteria (comma-separated)</label>
          <input
            type="text"
            value={settings.decide_defaults.criteria.join(', ')}
            onChange={(e) =>
              updateField(
                'decide_defaults.criteria',
                e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
              )
            }
          />
        </div>

        <h4>Brainstorm Defaults</h4>
        <div className="form-group">
          <label>Default Style</label>
          <select
            value={settings.brainstorm_defaults.style}
            onChange={(e) => updateField('brainstorm_defaults.style', e.target.value)}
          >
            <option value="wild">Wild</option>
            <option value="practical">Practical</option>
            <option value="balanced">Balanced</option>
          </select>
        </div>
        <div className="form-group">
          <label>Default Rounds</label>
          <input
            type="number"
            min={1}
            max={5}
            value={settings.brainstorm_defaults.rounds}
            onChange={(e) => updateField('brainstorm_defaults.rounds', Number(e.target.value))}
          />
        </div>
      </section>

      {/* Model Settings */}
      <section className="settings-section">
        <h3>Model Parameters</h3>
        <div className="form-group">
          <label>Max Tokens</label>
          <input
            type="number"
            value={settings.model_settings.max_tokens}
            onChange={(e) => updateField('model_settings.max_tokens', Number(e.target.value))}
          />
        </div>
        <div className="form-group">
          <label>Temperature</label>
          <input
            type="number"
            step={0.1}
            min={0}
            max={2}
            value={settings.model_settings.temperature}
            onChange={(e) => updateField('model_settings.temperature', Number(e.target.value))}
          />
        </div>
        <div className="form-group">
          <label>Timeout (seconds)</label>
          <input
            type="number"
            value={settings.model_settings.timeout_seconds}
            onChange={(e) => updateField('model_settings.timeout_seconds', Number(e.target.value))}
          />
        </div>
      </section>

      <div className="settings-actions">
        <button onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
        {message && <span className="settings-message">{message}</span>}
      </div>
    </div>
  );
}
