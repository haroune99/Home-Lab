import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

export function ModelsPage() {
  const qc = useQueryClient();
  const [pullModel, setPullModel] = useState('');
  const [pullNode, setPullNode] = useState<'mac' | 'hp'>('mac');

  const { data: models, isLoading } = useQuery({
    queryKey: ['models'],
    queryFn: api.models,
    refetchInterval: 10000,
  });

  const pullMutation = useMutation({
    mutationFn: () => api.pullModel(pullModel, pullNode),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['models'] }),
  });

  const macNames = new Set(models?.mac.map((m) => m.name) ?? []);
  const hpNames = new Set(models?.hp.map((m) => m.name) ?? []);
  const allNames = new Set([...macNames, ...hpNames]);

  const formatSize = (bytes: number | null) => {
    if (!bytes) return '—';
    return `${(bytes / 1e9).toFixed(1)} GB`;
  };

  return (
    <div>
      <h2 className="mb-6 text-2xl font-bold">Models</h2>

      <div className="mb-6 flex flex-wrap items-end gap-3 rounded-xl border border-zinc-800 bg-zinc-900/80 p-4">
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Model name</label>
          <input
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm"
            placeholder="qwen3:8b"
            value={pullModel}
            onChange={(e) => setPullModel(e.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Node</label>
          <select
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm"
            value={pullNode}
            onChange={(e) => setPullNode(e.target.value as 'mac' | 'hp')}
          >
            <option value="mac">Mac</option>
            <option value="hp">HP</option>
          </select>
        </div>
        <button
          className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium hover:bg-sky-500 disabled:opacity-50"
          disabled={!pullModel || pullMutation.isPending}
          onClick={() => pullMutation.mutate()}
        >
          {pullMutation.isPending ? 'Pulling…' : 'Pull model'}
        </button>
        {pullMutation.isError && (
          <p className="text-sm text-red-400">{(pullMutation.error as Error).message}</p>
        )}
      </div>

      {isLoading ? (
        <p className="text-zinc-500">Loading…</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-zinc-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800 bg-zinc-900/80 text-left text-zinc-400">
                <th className="px-4 py-3">Model</th>
                <th className="px-4 py-3">Mac</th>
                <th className="px-4 py-3">HP</th>
                <th className="px-4 py-3">Mac size</th>
                <th className="px-4 py-3">HP size</th>
              </tr>
            </thead>
            <tbody>
              {[...allNames].sort().map((name) => {
                const macModel = models?.mac.find((m) => m.name === name);
                const hpModel = models?.hp.find((m) => m.name === name);
                const onBoth = macNames.has(name) && hpNames.has(name);
                return (
                  <tr key={name} className="border-b border-zinc-800/50 hover:bg-zinc-900/40">
                    <td className="px-4 py-3 font-medium">
                      {name}
                      {onBoth && (
                        <span className="ml-2 rounded bg-sky-500/20 px-1.5 py-0.5 text-xs text-sky-300">
                          both
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">{macNames.has(name) ? '✓' : '—'}</td>
                    <td className="px-4 py-3">{hpNames.has(name) ? '✓' : '—'}</td>
                    <td className="px-4 py-3">{formatSize(macModel?.size ?? null)}</td>
                    <td className="px-4 py-3">{formatSize(hpModel?.size ?? null)}</td>
                  </tr>
                );
              })}
              {allNames.size === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-zinc-500">
                    No models found. Pull one above or run ./scripts/pull-models.sh
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
