const API_BASE = import.meta.env.VITE_API_URL || '';

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  return res.json();
}

export interface NodeStatus {
  id: string;
  display_name: string;
  online: boolean;
  ollama_online: boolean;
  agent_online: boolean | null;
  latency_ms: number | null;
  cpu_percent: number | null;
  ram_used_mb: number | null;
  ram_total_mb: number | null;
  ram_used_percent: number | null;
  ollama_version: string | null;
  ollama_loaded_model: string | null;
  error: string | null;
}

export interface ModelInfo {
  name: string;
  size: number | null;
  modified_at: string | null;
}

export interface ModelsByNode {
  mac: ModelInfo[];
  hp: ModelInfo[];
}

export interface AvailableModels {
  mac: string[];
  hp: string[];
  all_models: string[];
}

export interface MetricsSummary {
  requests_today: number;
  avg_tokens_per_sec: number | null;
  avg_latency_ms: number | null;
  total_requests: number;
}

export interface InferenceLogEntry {
  id: number;
  timestamp: string;
  node: string;
  model: string;
  routing_mode: string;
  routing_reason: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  latency_ms: number;
  tokens_per_sec: number | null;
  status: string;
  error: string | null;
}

export interface TimeseriesPoint {
  timestamp: string;
  node?: string | null;
  model?: string | null;
  avg_latency_ms: number | null;
  avg_tokens_per_sec: number | null;
  count: number;
}

export interface RoutingPreview {
  node: string;
  routing_mode: string;
  routing_reason: string;
  model_available: boolean;
}

export interface InferenceResult {
  node: string;
  model: string;
  routing_mode: string;
  routing_reason: string | null;
  response: string;
  prompt_tokens: number;
  completion_tokens: number;
  latency_ms: number;
  tokens_per_sec: number | null;
}

export const api = {
  health: () => fetchJson<{ status: string }>('/api/v1/health'),
  nodes: () => fetchJson<NodeStatus[]>('/api/v1/nodes'),
  models: () => fetchJson<ModelsByNode>('/api/v1/models'),
  availableModels: () => fetchJson<AvailableModels>('/api/v1/models/available'),
  pullModel: (model: string, node: string) =>
    fetchJson('/api/v1/models/pull', {
      method: 'POST',
      body: JSON.stringify({ model, node }),
    }),
  metricsSummary: () => fetchJson<MetricsSummary>('/api/v1/metrics/summary'),
  inferenceLogs: (params?: { limit?: number; node?: string; model?: string }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.node) q.set('node', params.node);
    if (params?.model) q.set('model', params.model);
    return fetchJson<InferenceLogEntry[]>(`/api/v1/metrics/inference?${q}`);
  },
  timeseries: (groupBy: 'hour' | 'node' | 'model' = 'hour') =>
    fetchJson<TimeseriesPoint[]>(`/api/v1/metrics/timeseries?group_by=${groupBy}`),
  routingPreview: (model: string, node: string) =>
    fetchJson<RoutingPreview>('/api/v1/inference/preview', {
      method: 'POST',
      body: JSON.stringify({ model, node }),
    }),
  inference: (body: { model: string; prompt: string; node: string; stream?: boolean }) =>
    fetchJson<InferenceResult>('/api/v1/inference', {
      method: 'POST',
      body: JSON.stringify({ ...body, stream: false }),
    }),
  inferenceStream: async (
    body: { model: string; prompt: string; node: string },
    onEvent: (event: Record<string, unknown>) => void,
  ) => {
    const res = await fetch(`${API_BASE}/api/v1/inference`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...body, stream: true }),
    });
    if (!res.ok) throw new Error(await res.text());
    const reader = res.body?.getReader();
    if (!reader) throw new Error('No response body');
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            onEvent(JSON.parse(line.slice(6)));
          } catch {
            /* skip */
          }
        }
      }
    }
  },
};
