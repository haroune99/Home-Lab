import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { api } from '../api/client';

export function InferencePage() {
  const [nodeFilter, setNodeFilter] = useState<string>('');

  const { data: logs } = useQuery({
    queryKey: ['inference-logs', nodeFilter],
    queryFn: () =>
      api.inferenceLogs({ limit: 100, node: nodeFilter || undefined }),
    refetchInterval: 5000,
  });

  const { data: byNode } = useQuery({
    queryKey: ['timeseries-node'],
    queryFn: () => api.timeseries('node'),
    refetchInterval: 10000,
  });

  const chartData =
    byNode?.map((p) => ({
      name: p.node ?? '?',
      tok_s: p.avg_tokens_per_sec ? Math.round(p.avg_tokens_per_sec * 10) / 10 : 0,
      latency: p.avg_latency_ms ? Math.round(p.avg_latency_ms) : 0,
      count: p.count,
    })) ?? [];

  return (
    <div>
      <h2 className="mb-6 text-2xl font-bold">Inference Log</h2>

      <div className="mb-6 rounded-xl border border-zinc-800 bg-zinc-900/80 p-4">
        <h3 className="mb-4 text-sm font-medium text-zinc-400">Avg tokens/sec by node</h3>
        {chartData.length === 0 ? (
          <p className="text-sm text-zinc-500">No inference data yet — run something in Playground</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="name" stroke="#71717a" fontSize={11} />
              <YAxis stroke="#71717a" fontSize={11} />
              <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #3f3f46' }} />
              <Bar dataKey="tok_s" fill="#38bdf8" name="tok/s" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="mb-4 flex gap-2">
        <select
          className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm"
          value={nodeFilter}
          onChange={(e) => setNodeFilter(e.target.value)}
        >
          <option value="">All nodes</option>
          <option value="mac">Mac</option>
          <option value="hp">HP</option>
          <option value="air">Air</option>
        </select>
      </div>

      <div className="overflow-x-auto rounded-xl border border-zinc-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/80 text-left text-zinc-400">
              <th className="px-3 py-2">Time</th>
              <th className="px-3 py-2">Node</th>
              <th className="px-3 py-2">Model</th>
              <th className="px-3 py-2">Mode</th>
              <th className="px-3 py-2">Tok/s</th>
              <th className="px-3 py-2">Latency</th>
              <th className="px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {logs?.map((log) => (
              <tr key={log.id} className="border-b border-zinc-800/50 hover:bg-zinc-900/40">
                <td className="px-3 py-2 text-zinc-400">{log.timestamp.slice(0, 19)}</td>
                <td className="px-3 py-2">{log.node}</td>
                <td className="px-3 py-2">{log.model}</td>
                <td className="px-3 py-2">
                  <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs">{log.routing_mode}</span>
                </td>
                <td className="px-3 py-2">{log.tokens_per_sec?.toFixed(1) ?? '—'}</td>
                <td className="px-3 py-2">{log.latency_ms.toFixed(0)} ms</td>
                <td className="px-3 py-2">
                  <span
                    className={
                      log.status === 'success' ? 'text-emerald-400' : 'text-red-400'
                    }
                  >
                    {log.status}
                  </span>
                </td>
              </tr>
            ))}
            {(!logs || logs.length === 0) && (
              <tr>
                <td colSpan={7} className="px-3 py-8 text-center text-zinc-500">
                  No inference runs yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
