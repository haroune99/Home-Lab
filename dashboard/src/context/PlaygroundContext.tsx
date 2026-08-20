import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { api } from '../api/client';

export type NodeChoice = 'mac' | 'hp' | 'air' | 'auto';

export interface PlaygroundStats {
  latency_ms?: number;
  tokens_per_sec?: number;
}

interface PlaygroundState {
  node: NodeChoice;
  model: string;
  prompt: string;
  response: string;
  routingReason: string | null;
  routingNode: string | null;
  loading: boolean;
  stats: PlaygroundStats | null;
  error: string | null;
}

interface PlaygroundContextValue extends PlaygroundState {
  setNode: (node: NodeChoice) => void;
  setModel: (model: string) => void;
  setPrompt: (prompt: string) => void;
  runInference: () => Promise<void>;
  clearSession: () => void;
}

const STORAGE_KEY = 'homelab-playground';

const DEFAULT_PROMPT = 'Explain what a home lab is in one sentence.';

const defaultState: PlaygroundState = {
  node: 'auto',
  model: '',
  prompt: DEFAULT_PROMPT,
  response: '',
  routingReason: null,
  routingNode: null,
  loading: false,
  stats: null,
  error: null,
};

function loadPersisted(): Partial<PlaygroundState> {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Partial<PlaygroundState>;
    return { ...parsed, loading: false };
  } catch {
    return {};
  }
}

function persist(state: PlaygroundState) {
  try {
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        node: state.node,
        model: state.model,
        prompt: state.prompt,
        response: state.response,
        routingReason: state.routingReason,
        routingNode: state.routingNode,
        stats: state.stats,
        error: state.error,
      }),
    );
  } catch {
    /* quota or private mode */
  }
}

const PlaygroundContext = createContext<PlaygroundContextValue | null>(null);

export function PlaygroundProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<PlaygroundState>(() => ({
    ...defaultState,
    ...loadPersisted(),
  }));
  const runIdRef = useRef(0);
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    const delay = state.loading ? 400 : 0;
    const id = setTimeout(() => {
      if (!state.loading || state.response) {
        persist(state);
      }
    }, delay);
    return () => clearTimeout(id);
  }, [state]);

  // Refresh routing preview when node/model change (not during inference)
  useEffect(() => {
    if (state.loading || !state.model) return;

    if (state.node === 'auto') {
      let cancelled = false;
      api.routingPreview(state.model, 'auto').then((p) => {
        if (!cancelled) {
          setState((s) => ({
            ...s,
            routingNode: p.node,
            routingReason: p.routing_reason,
          }));
        }
      });
      return () => {
        cancelled = true;
      };
    }

    setState((s) => ({
      ...s,
      routingNode: s.node,
      routingReason: `${s.node}: explicitly selected`,
    }));
  }, [state.node, state.model, state.loading]);

  const patch = useCallback((partial: Partial<PlaygroundState>) => {
    setState((s) => ({ ...s, ...partial }));
  }, []);

  const runInference = useCallback(async () => {
    const { model, prompt, node } = stateRef.current;
    if (!model || !prompt) return;

    const runId = ++runIdRef.current;

    patch({
      loading: true,
      response: '',
      stats: null,
      error: null,
    });

    try {
      await api.inferenceStream({ model, prompt, node }, (event) => {
        if (runId !== runIdRef.current) return;

        if (event.type === 'meta') {
          patch({
            routingNode: event.node as string,
            routingReason: event.routing_reason as string,
          });
        } else if (event.type === 'token') {
          setState((s) => ({
            ...s,
            response: s.response + (event.token as string),
          }));
        } else if (event.type === 'done') {
          patch({
            stats: {
              latency_ms: event.latency_ms as number,
              tokens_per_sec: event.tokens_per_sec as number,
            },
          });
        } else if (event.type === 'error') {
          patch({ error: event.error as string });
        }
      });
    } catch (e) {
      if (runId === runIdRef.current) {
        patch({ error: (e as Error).message });
      }
    } finally {
      if (runId === runIdRef.current) {
        patch({ loading: false });
      }
    }
  }, [patch]);

  const clearSession = useCallback(() => {
    runIdRef.current += 1;
    sessionStorage.removeItem(STORAGE_KEY);
    setState({ ...defaultState });
  }, []);

  const value = useMemo<PlaygroundContextValue>(
    () => ({
      ...state,
      setNode: (node) => patch({ node }),
      setModel: (model) => patch({ model }),
      setPrompt: (prompt) => patch({ prompt }),
      runInference,
      clearSession,
    }),
    [state, patch, runInference, clearSession],
  );

  return (
    <PlaygroundContext.Provider value={value}>{children}</PlaygroundContext.Provider>
  );
}

export function usePlayground() {
  const ctx = useContext(PlaygroundContext);
  if (!ctx) {
    throw new Error('usePlayground must be used within PlaygroundProvider');
  }
  return ctx;
}

export function usePlaygroundLoading() {
  const ctx = useContext(PlaygroundContext);
  return ctx?.loading ?? false;
}
