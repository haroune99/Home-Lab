import { NavLink } from 'react-router-dom';
import { usePlaygroundLoading } from '../context/PlaygroundContext';

const links = [
  { to: '/', label: 'Overview' },
  { to: '/nodes', label: 'Nodes' },
  { to: '/models', label: 'Models' },
  { to: '/playground', label: 'Playground' },
  { to: '/inference', label: 'Inference' },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const playgroundLoading = usePlaygroundLoading();

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r border-zinc-800 bg-zinc-900/50 p-4">
        <h1 className="mb-6 text-lg font-bold tracking-tight">
          <span className="text-sky-400">Home</span> Lab
        </h1>
        <nav className="space-y-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) =>
                `flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-sky-500/20 text-sky-300'
                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                }`
              }
            >
              <span>{l.label}</span>
              {l.to === '/playground' && playgroundLoading && (
                <span className="h-2 w-2 animate-pulse rounded-full bg-amber-400" title="Inference running" />
              )}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
