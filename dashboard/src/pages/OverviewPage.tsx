import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { NodeCard } from '../components/NodeCard';
import { StatCard } from '../components/StatCard';

export function OverviewPage() {
  const { data: nodes } = useQuery({
    queryKey: ['nodes'],
    queryFn: api.nodes,
    refetchInterval: 5000,
  });

  const { data: summary } = useQuery({
    queryKey: ['metrics-summary'],
    queryFn: api.metricsSummary,
    refetchInterval: 5000,
  });

  const total = nodes?.length ?? 3;
  const onlineCount = nodes?.filter((n) => n.online).length ?? 0;

  return (
    <div>
      <h2 className="mb-6 text-2xl font-bold">Overview</h2>

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Nodes online"
          value={`${onlineCount} / ${total}`}
          accent={
            onlineCount === total ? 'green' : onlineCount === 0 ? 'red' : 'yellow'
          }
        />
        <StatCard label="Requests today" value={summary?.requests_today ?? 0} />
        <StatCard
          label="Avg tokens/sec"
          value={summary?.avg_tokens_per_sec?.toFixed(1) ?? '-'}
        />
        <StatCard
          label="Avg latency"
          value={summary?.avg_latency_ms ? `${summary.avg_latency_ms.toFixed(0)} ms` : '-'}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {nodes?.map((node) => (
          <NodeCard key={node.id} node={node} />
        ))}
      </div>
    </div>
  );
}
