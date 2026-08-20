import { useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { usePlayground, type NodeChoice } from '../context/PlaygroundContext';

export function PlaygroundPage() {
  const {
    node,
    model,
    prompt,
    response,
    routingReason,
    routingNode,
    loading,
    stats,
    error,
    setNode,
    setModel,
    setPrompt,
    runInference,
    clearSession,
  } = usePlayground();

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
    if (node === 'air') return available.air;
    return available.all_models;
  }, [available, node]);

  useEffect(() => {
    if (modelOptions.length && !modelOptions.includes(model)) {
      setModel(modelOptions[0]);
    }
  }, [modelOptions, model, setModel]);

  const shortModelLabel = (name: string) => {
    if (name.includes('/')) return name.split('/').pop() || name;
    return name;
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
              disabled={loading}
            >
              <option value="auto">Auto (orchestrator)</option>
              <option value="mac">Mac M2 Pro</option>
              <option value="hp">HP Ultra 7</option>
              <option value="air">MacBook Air (Intel)</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs text-zinc-500">Model</label>
            <select
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={loading}
            >
              {modelOptions.map((m) => (
                <option key={m} value={m}>
                  {shortModelLabel(m)}
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

          {loading && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">
              Inference running on <strong>{routingNode ?? node}</strong> — safe to switch tabs
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
              className="h-32 w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm disabled:opacity-60"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="flex gap-3">
            <button
              className="rounded-lg bg-emerald-600 px-6 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
              disabled={loading || !model || !prompt}
              onClick={() => runInference()}
            >
              {loading ? 'Running…' : 'Run inference'}
            </button>
            {(response || stats || error) && !loading && (
              <button
                className="rounded-lg border border-zinc-600 px-4 py-2 text-sm text-zinc-400 hover:bg-zinc-800"
                onClick={clearSession}
              >
                Clear
              </button>
            )}
          </div>

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
              {response || (loading ? 'Generating…' : 'Response will appear here')}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
