import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, AlertTriangle } from "lucide-react";
import { useGetTrace, getGetTraceQueryKey } from "@workspace/api-client-react";
import { format } from "date-fns";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PageHeader } from "@/components/page-header";

const TRACE_PARAMS = { limit: 500 } as const;

interface Failure {
  eventId: string;
  time: string;
  reason: string;
  kind: "behavior" | "tool" | "patch";
  subject: string;
  message: string;
}

export default function Failures() {
  const [open, setOpen] = useState<string | null>(null);

  const { data: trace, isLoading } = useGetTrace(TRACE_PARAMS, {
    query: { refetchInterval: 5000, queryKey: getGetTraceQueryKey(TRACE_PARAMS) },
  });

  const failures = useMemo<Failure[]>(() => {
    const out: Failure[] = [];
    for (const e of trace?.events ?? []) {
      const p = (e.payload ?? {}) as Record<string, any>;
      if (e.event_type === "behavior.failed") {
        out.push({
          eventId: e.id,
          time: e.timestamp,
          reason: (p.reason ?? p.exception_type ?? "ERROR") as string,
          kind: "behavior",
          subject: (p.behavior ?? "?") as string,
          message: (p.message ?? p.exception_type ?? "") as string,
        });
      } else if (e.event_type === "tool.responded" && p.error) {
        out.push({
          eventId: e.id,
          time: e.timestamp,
          reason: (p.error.reason ?? "tool.error") as string,
          kind: "tool",
          subject: (p.tool ?? p.behavior ?? "?") as string,
          message: (p.error.message ?? JSON.stringify(p.error)) as string,
        });
      } else if (e.event_type === "patch.rejected") {
        out.push({
          eventId: e.id,
          time: e.timestamp,
          reason: "patch.rejected",
          kind: "patch",
          subject: (p.target ?? p.patch_id ?? "?") as string,
          message: (p.reason ?? "") as string,
        });
      }
    }
    return out;
  }, [trace]);

  const byReason = useMemo(() => {
    const c = new Map<string, number>();
    failures.forEach((f) => c.set(f.reason, (c.get(f.reason) ?? 0) + 1));
    return [...c.entries()].sort((a, b) => b[1] - a[1]);
  }, [failures]);

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="FAILURES" concept="failures" subtitle={`${failures.length} TOTAL`} />

      <ScrollArea className="flex-1">
        {isLoading && !trace ? (
          <div className="p-4 space-y-2">
            {[1, 2, 3].map((i) => <div key={i} className="h-12 bg-muted animate-pulse border border-border" />)}
          </div>
        ) : failures.length > 0 ? (
          <div>
            <div className="flex flex-wrap gap-2 border-b border-border p-4">
              {byReason.map(([reason, count]) => (
                <div key={reason} className="border border-destructive/30 bg-destructive/5 px-3 py-1.5 font-mono text-xs">
                  <span className="text-destructive">{reason}</span>
                  <span className="ml-2 text-muted-foreground">{count}</span>
                </div>
              ))}
            </div>
            <div className="divide-y divide-border font-mono">
              {failures.map((f) => {
                const isOpen = open === f.eventId;
                return (
                  <div key={f.eventId}>
                    <button
                      onClick={() => setOpen(isOpen ? null : f.eventId)}
                      className={`flex w-full items-center gap-3 px-4 py-3 text-left text-xs transition-colors ${isOpen ? "bg-destructive/5" : "hover:bg-muted/50"}`}
                    >
                      {isOpen ? <ChevronDown className="h-3.5 w-3.5 shrink-0 text-destructive" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />}
                      <span className="w-24 shrink-0 text-muted-foreground">{format(new Date(f.time), "HH:mm:ss.SSS")}</span>
                      <AlertTriangle className="h-3 w-3 shrink-0 text-destructive" />
                      <span className="border border-destructive/40 bg-destructive/10 px-2 py-0.5 text-[10px] tracking-wider text-destructive">{f.reason}</span>
                      <span className="text-foreground truncate">{f.subject}</span>
                      <span className="ml-auto shrink-0 text-[10px] uppercase text-muted-foreground/60">{f.kind}</span>
                    </button>
                    {isOpen && (
                      <div className="border-t border-border bg-card px-4 py-3 pl-11 text-xs">
                        <pre className="overflow-x-auto whitespace-pre-wrap break-all text-muted-foreground">{f.message || "(no message)"}</pre>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="flex h-64 flex-col items-center justify-center gap-1 text-muted-foreground font-mono text-sm">
            <span className="text-green-400">NO_FAILURES</span>
            <span className="text-xs text-muted-foreground/70">This run completed without behavior errors, tool errors, or rejected patches.</span>
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
