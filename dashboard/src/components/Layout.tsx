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
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="shrink-0 border-b border-zinc-800 bg-zinc-900/50 p-3 md:w-56 md:border-b-0 md:border-r md:p-4">
        <h1 className="mb-3 text-lg font-bold tracking-tight md:mb-6">
          <span className="text-sky-400">Home</span> Lab
        </h1>
        <nav className="flex gap-1 overflow-x-auto md:flex-col md:space-y-1 md:overflow-visible">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) =>
                `flex shrink-0 items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-sky-500/20 text-sky-300'
                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                }`
              }
            >
              <span>{l.label}</span>
              {l.to === '/playground' && playgroundLoading && (
                <span
                  className="ml-2 h-2 w-2 animate-pulse rounded-full bg-amber-400"
                  title="Inference running"
                />
              )}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
    </div>
  );
}
