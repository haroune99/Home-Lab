import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

type NodeChoice = 'mac' | 'hp' | 'auto';

export function PlaygroundPage() {
  const [node, setNode] = useState<NodeChoice>('auto');
  const [model, setModel] = useState('');
  const [prompt, setPrompt] = useState('Explain what a home lab is in one sentence.');
  const [response, setResponse] = useState('');
  const [routingReason, setRoutingReason] = useState<string | null>(null);
  const [routingNode, setRoutingNode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<{ latency_ms?: number; tokens_per_sec?: number } | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);

  const { data: nodes } = useQuery({
    queryKey: ['nodes'],
    queryFn: api.nodes,
    refetchInterval: 5000,
  });

  const { data: available } = useQuery({
    queryKey: ['available-models'],
    queryFn: api.availableModels,
    refetchInterval: 10000,
  });

  const modelOptions = useMemo(() => {
    if (!available) return [];
    if (node === 'mac') return available.mac;
    if (node === 'hp') return available.hp;
    return available.all_models;
  }, [available, node]);

  useEffect(() => {
    if (modelOptions.length && !modelOptions.includes(model)) {
      setModel(modelOptions[0]);
    }
  }, [modelOptions, model]);

  useEffect(() => {
    if (node === 'auto' && model) {
      api.routingPreview(model, 'auto').then((p) => {
        setRoutingReason(p.routing_reason);
        setRoutingNode(p.node);
      });
    } else {
      setRoutingReason(null);
      setRoutingNode(node === 'auto' ? null : node);
    }
  }, [node, model]);

  const runStream = async () => {
    setLoading(true);
    setResponse('');
    setStats(null);
    setError(null);
    setRoutingReason(null);

    try {
      await api.inferenceStream({ model, prompt, node }, (event) => {
        if (event.type === 'meta') {
          setRoutingNode(event.node as string);
          setRoutingReason(event.routing_reason as string);
        } else if (event.type === 'token') {
          setResponse((r) => r + (event.token as string));
        } else if (event.type === 'done') {
          setStats({
            latency_ms: event.latency_ms as number,
            tokens_per_sec: event.tokens_per_sec as number,
          });
        } else if (event.type === 'error') {
          setError(event.error as string);
        }
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="mb-6 text-2xl font-bold">Playground</h2>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-1">
          <div>
            <label className="mb-1 block text-xs text-zinc-500">Node</label>
            <select
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm"
              value={node}
              onChange={(e) => setNode(e.target.value as NodeChoice)}
            >
              <option value="auto">Auto (orchestrator)</option>
              <option value="mac">Mac M2 Pro</option>
              <option value="hp">HP Ultra 7</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs text-zinc-500">Model</label>
            <select
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              {modelOptions.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          {(routingReason || routingNode) && (
            <div className="rounded-lg border border-sky-500/30 bg-sky-500/10 p-3 text-sm">
              <p className="text-sky-300">
                {node === 'auto' ? 'Auto route' : 'Manual'} → <strong>{routingNode}</strong>
              </p>
              {routingReason && <p className="mt-1 text-zinc-400">{routingReason}</p>}
            </div>
          )}

          <div className="space-y-2 text-xs text-zinc-500">
            {nodes?.map((n) => (
              <div key={n.id} className="flex justify-between">
                <span>{n.display_name}</span>
                <span>
                  {n.ram_used_percent?.toFixed(0) ?? '?'}% RAM · {n.ollama_loaded_model ?? 'idle'}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4 lg:col-span-2">
          <div>
            <label className="mb-1 block text-xs text-zinc-500">Prompt</label>
            <textarea
              className="h-32 w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>

          <button
            className="rounded-lg bg-emerald-600 px-6 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
            disabled={loading || !model || !prompt}
            onClick={runStream}
          >
            {loading ? 'Running…' : 'Run inference'}
          </button>

          {error && <p className="text-sm text-red-400">{error}</p>}

          {stats && (
            <p className="text-sm text-zinc-400">
              {stats.latency_ms?.toFixed(0)} ms
              {stats.tokens_per_sec != null && ` · ${stats.tokens_per_sec.toFixed(1)} tok/s`}
            </p>
          )}

          <div>
            <label className="mb-1 block text-xs text-zinc-500">Response</label>
            <div className="min-h-[200px] whitespace-pre-wrap rounded-lg border border-zinc-700 bg-zinc-900 p-4 text-sm">
              {response || (loading ? '…' : 'Response will appear here')}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
