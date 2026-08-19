interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent?: 'green' | 'red' | 'yellow' | 'blue';
}

const accentMap = {
  green: 'border-emerald-500/50 text-emerald-400',
  red: 'border-red-500/50 text-red-400',
  yellow: 'border-amber-500/50 text-amber-400',
  blue: 'border-sky-500/50 text-sky-400',
};

export function StatCard({ label, value, sub, accent }: StatCardProps) {
  return (
    <div className={`rounded-xl border bg-zinc-900/80 p-4 ${accent ? accentMap[accent] : 'border-zinc-800'}`}>
      <p className="text-xs uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
      {sub && <p className="mt-1 text-sm text-zinc-400">{sub}</p>}
    </div>
  );
}
