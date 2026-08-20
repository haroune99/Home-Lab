import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { api } from '../api/client';
import { NodeCard } from '../components/NodeCard';

export function NodesPage() {
  const { data: nodes } = useQuery({
    queryKey: ['nodes'],
    queryFn: api.nodes,
    refetchInterval: 5000,
  });

  const { data: snapshots } = useQuery({
    queryKey: ['snapshots'],
    queryFn: async () => {
      const res = await fetch('/api/v1/metrics/snapshots?limit=60');
      return res.json() as Promise<
        Array<{ timestamp: string; node: string; ram_used_mb: number; cpu_percent: number }>
      >;
    },
    refetchInterval: 10000,
  });

  const macHistory =
    snapshots
      ?.filter((s) => s.node === 'mac')
      .reverse()
      .map((s) => ({
        time: s.timestamp.slice(11, 16),
        ram: Math.round((s.ram_used_mb / 1024) * 10) / 10,
        cpu: s.cpu_percent,
      })) ?? [];

  const hpHistory =
    snapshots
      ?.filter((s) => s.node === 'hp')
      .reverse()
      .map((s) => ({
        time: s.timestamp.slice(11, 16),
        ram: Math.round((s.ram_used_mb / 1024) * 10) / 10,
        cpu: s.cpu_percent,
      })) ?? [];

  return (
    <div>
      <h2 className="mb-6 text-2xl font-bold">Nodes</h2>

      <div className="mb-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {nodes?.map((node) => (
          <NodeCard key={node.id} node={node} />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartPanel title="Mac — RAM (GB)" data={macHistory} dataKey="ram" color="#38bdf8" />
        <ChartPanel title="HP — RAM (GB)" data={hpHistory} dataKey="ram" color="#a78bfa" />
      </div>
    </div>
  );
}

function ChartPanel({
  title,
  data,
  dataKey,
  color,
}: {
  title: string;
  data: Array<{ time: string; ram: number; cpu: number }>;
  dataKey: string;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/80 p-4">
      <h3 className="mb-4 text-sm font-medium text-zinc-400">{title}</h3>
      {data.length === 0 ? (
        <p className="text-sm text-zinc-500">Collecting snapshots…</p>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis dataKey="time" stroke="#71717a" fontSize={11} />
            <YAxis stroke="#71717a" fontSize={11} />
            <Tooltip
              contentStyle={{ background: '#18181b', border: '1px solid #3f3f46' }}
            />
            <Line type="monotone" dataKey={dataKey} stroke={color} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
