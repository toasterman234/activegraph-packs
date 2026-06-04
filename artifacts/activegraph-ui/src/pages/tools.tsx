import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Wrench } from "lucide-react";
import { useGetTrace, getGetTraceQueryKey } from "@workspace/api-client-react";
import { format } from "date-fns";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PageHeader } from "@/components/page-header";

const TRACE_PARAMS = { limit: 500 } as const;

interface ToolPayload {
  behavior?: string | null;
  tool?: string | null;
  cache_hit?: boolean | null;
  latency_seconds?: number | null;
  cost_usd?: number | null;
  error?: { reason?: string; message?: string } | null;
}

export default function Tools() {
  const [open, setOpen] = useState<string | null>(null);

  const { data: trace, isLoading } = useGetTrace(TRACE_PARAMS, {
    query: { refetchInterval: 5000, queryKey: getGetTraceQueryKey(TRACE_PARAMS) },
  });

  const calls = useMemo(
    () =>
      (trace?.events ?? [])
        .filter((e) => e.event_type === "tool.responded")
        .map((e) => ({
          eventId: e.id,
          time: e.timestamp,
          payload: (e.payload ?? {}) as ToolPayload,
        })),
    [trace]
  );

  const byTool = useMemo(() => {
    const c = new Map<string, number>();
    calls.forEach(({ payload }) => {
      const t = payload.tool ?? "unknown";
      c.set(t, (c.get(t) ?? 0) + 1);
    });
    return [...c.entries()].sort((a, b) => b[1] - a[1]);
  }, [calls]);

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="TOOLS" concept="tools" subtitle={`${calls.length} CALLS`} />

      <div className="flex flex-1 min-h-0">
        {byTool.length > 0 && (
          <aside className="hidden lg:flex w-56 shrink-0 flex-col border-r border-border p-3 overflow-auto">
            <div className="px-1 pb-2 text-[10px] tracking-widest text-muted-foreground">TOOLS USED</div>
            {byTool.map(([tool, count]) => (
              <div key={tool} className="flex items-center justify-between px-2 py-1.5 text-xs font-mono text-muted-foreground">
                <span className="truncate">{tool}</span>
                <span>{count}</span>
              </div>
            ))}
          </aside>
        )}

        <ScrollArea className="flex-1">
          {isLoading && !trace ? (
            <div className="p-4 space-y-2">
              {[1, 2, 3].map((i) => <div key={i} className="h-12 bg-muted animate-pulse border border-border" />)}
            </div>
          ) : calls.length > 0 ? (
            <div className="divide-y divide-border font-mono">
              {calls.map(({ eventId, time, payload }) => {
                const isOpen = open === eventId;
                const errored = !!payload.error;
                return (
                  <div key={eventId}>
                    <button
                      onClick={() => setOpen(isOpen ? null : eventId)}
                      className={`flex w-full items-center gap-3 px-4 py-3 text-left text-xs transition-colors ${isOpen ? "bg-primary/5" : "hover:bg-muted/50"}`}
                    >
                      {isOpen ? <ChevronDown className="h-3.5 w-3.5 shrink-0 text-primary" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />}
                      <span className="w-24 shrink-0 text-muted-foreground">{format(new Date(time), "HH:mm:ss.SSS")}</span>
                      <Wrench className="h-3 w-3 shrink-0 text-primary" />
                      <span className="text-foreground truncate">{payload.tool ?? "unknown"}</span>
                      {payload.behavior && <span className="hidden sm:inline text-muted-foreground truncate">{payload.behavior}</span>}
                      <span className="ml-auto flex shrink-0 items-center gap-2">
                        {payload.cache_hit && <span className="text-[10px] text-muted-foreground">CACHE</span>}
                        {payload.latency_seconds != null && !payload.cache_hit && (
                          <span className="text-[10px] text-muted-foreground">{payload.latency_seconds.toFixed(1)}s</span>
                        )}
                        <span className={`border px-2 py-0.5 text-[10px] tracking-wider ${errored ? "border-destructive/40 bg-destructive/10 text-destructive" : "border-green-500/40 bg-green-500/10 text-green-400"}`}>
                          {errored ? "ERROR" : "OK"}
                        </span>
                      </span>
                    </button>
                    {isOpen && (
                      <div className="border-t border-border bg-card px-4 py-3 pl-11 text-xs">
                        <pre className="overflow-x-auto whitespace-pre-wrap break-all text-muted-foreground">
                          {JSON.stringify(payload, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex h-64 flex-col items-center justify-center gap-1 text-muted-foreground font-mono text-sm">
              <span>NO_TOOL_CALLS</span>
              <span className="text-xs text-muted-foreground/70">This run executed no tools. Tool calls appear here as behaviors invoke them.</span>
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  );
}
