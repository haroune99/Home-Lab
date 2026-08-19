import type { NodeStatus } from '../api/client';

interface NodeCardProps {
  node: NodeStatus;
}

export function NodeCard({ node }: NodeCardProps) {
  const ramPct = node.ram_used_percent ?? 0;
  const ramColor =
    ramPct > 85 ? 'bg-red-500' : ramPct > 70 ? 'bg-amber-500' : 'bg-emerald-500';

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/80 p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">{node.display_name}</h3>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
            node.online ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
          }`}
        >
          {node.online ? 'Online' : 'Offline'}
        </span>
      </div>

      {node.error && (
        <p className="mt-2 text-sm text-red-400">{node.error}</p>
      )}

      <div className="mt-4 space-y-3 text-sm">
        <div>
          <div className="flex justify-between text-zinc-400">
            <span>RAM</span>
            <span>
              {node.ram_used_mb != null && node.ram_total_mb != null
                ? `${(node.ram_used_mb / 1024).toFixed(1)} / ${(node.ram_total_mb / 1024).toFixed(1)} GB`
                : '—'}
            </span>
          </div>
          <div className="mt-1 h-2 overflow-hidden rounded-full bg-zinc-800">
            <div className={`h-full ${ramColor}`} style={{ width: `${Math.min(ramPct, 100)}%` }} />
          </div>
        </div>

        <div className="flex justify-between">
          <span className="text-zinc-400">CPU</span>
          <span>{node.cpu_percent != null ? `${node.cpu_percent.toFixed(0)}%` : '—'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-zinc-400">Latency</span>
          <span>{node.latency_ms != null ? `${node.latency_ms.toFixed(0)} ms` : '—'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-zinc-400">Ollama</span>
          <span>{node.ollama_version ?? '—'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-zinc-400">Loaded model</span>
          <span className="truncate max-w-[160px] text-right">{node.ollama_loaded_model ?? 'none'}</span>
        </div>
      </div>
    </div>
  );
}
