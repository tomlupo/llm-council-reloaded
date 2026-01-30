const API_BASE = '/api';

export async function createConversation() {
  const res = await fetch(`${API_BASE}/conversations`, { method: 'POST' });
  return res.json();
}

export async function listConversations() {
  const res = await fetch(`${API_BASE}/conversations`);
  return res.json();
}

export async function getConversation(id) {
  const res = await fetch(`${API_BASE}/conversations/${id}`);
  return res.json();
}

export async function deleteConversation(id) {
  await fetch(`${API_BASE}/conversations/${id}`, { method: 'DELETE' });
}

export async function getSettings() {
  const res = await fetch(`${API_BASE}/settings`);
  return res.json();
}

export async function updateSettings(settings) {
  const res = await fetch(`${API_BASE}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  return res.json();
}

export async function getModels() {
  const res = await fetch(`${API_BASE}/models`);
  return res.json();
}

/** Full model lists per provider for searchable dropdowns. */
export async function getModelCatalog() {
  const res = await fetch(`${API_BASE}/model-catalog`);
  return res.json();
}

/**
 * Send a message and return an SSE event source.
 * Calls onEvent(eventName, data) for each SSE event.
 */
export function sendMessageStream(
  conversationId,
  { content, executionMode = 'full', deliberationMode = 'ask', modeConfig = null },
  onEvent,
  onDone,
  onError
) {
  const controller = new AbortController();

  fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content,
      execution_mode: executionMode,
      deliberation_mode: deliberationMode,
      mode_config: modeConfig,
    }),
    signal: controller.signal,
  })
    .then(async (response) => {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (currentEvent === 'done') {
                onDone?.(data);
              } else if (currentEvent === 'error') {
                onError?.(data);
              } else {
                onEvent?.(currentEvent, data);
              }
            } catch {
              // skip malformed JSON
            }
            currentEvent = '';
          }
        }
      }

      // Process remaining buffer
      if (buffer.trim()) {
        const remaining = buffer.split('\n');
        let currentEvent = '';
        for (const line of remaining) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (currentEvent === 'done') onDone?.(data);
              else if (currentEvent === 'error') onError?.(data);
              else onEvent?.(currentEvent, data);
            } catch {
              // skip
            }
          }
        }
      }

      onDone?.({ status: 'complete' });
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.({ message: err.message });
      }
    });

  return { abort: () => controller.abort() };
}
