import { useState, Fragment } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useGetTrace, getGetTraceQueryKey } from "@workspace/api-client-react";
import { format } from "date-fns";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PageHeader } from "@/components/page-header";

const TRACE_PARAMS = { limit: 500, event_type: "patch.applied" } as const;

interface PatchPayload {
  id?: string;
  target?: string;
  op?: string;
  value?: Record<string, unknown>;
  expected_version?: number | null;
  proposed_by?: string | null;
  rationale?: string | null;
  status?: string | null;
  rejection_reason?: string | null;
}

export default function Patches() {
  const [open, setOpen] = useState<string | null>(null);

  const { data: trace, isLoading } = useGetTrace(TRACE_PARAMS, {
    query: { refetchInterval: 5000, queryKey: getGetTraceQueryKey(TRACE_PARAMS) },
  });

  const patches = (trace?.events ?? []).map((e) => ({
    eventId: e.id,
    time: e.timestamp,
    patch: (e.payload?.patch ?? {}) as PatchPayload,
  }));

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="PATCHES" concept="patches" subtitle={`${patches.length} APPLIED`} />

      <ScrollArea className="flex-1">
        {isLoading && !trace ? (
          <div className="p-4 space-y-2">
            {[1, 2, 3, 4].map((i) => <div key={i} className="h-12 bg-muted animate-pulse border border-border" />)}
          </div>
        ) : patches.length > 0 ? (
          <div className="divide-y divide-border font-mono">
            {patches.map(({ eventId, time, patch }) => {
              const isOpen = open === eventId;
              const rejected = patch.status === "rejected";
              const fields = Object.entries(patch.value ?? {});
              return (
                <div key={eventId}>
                  <button
                    onClick={() => setOpen(isOpen ? null : eventId)}
                    className={`flex w-full items-center gap-3 px-4 py-3 text-left text-xs transition-colors ${
                      isOpen ? "bg-primary/5" : "hover:bg-muted/50"
                    }`}
                  >
                    {isOpen ? <ChevronDown className="h-3.5 w-3.5 shrink-0 text-primary" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />}
                    <span className="w-24 shrink-0 text-muted-foreground">{format(new Date(time), "HH:mm:ss.SSS")}</span>
                    <span className="text-foreground truncate">{patch.target ?? "-"}</span>
                    <span className="text-muted-foreground/60">·</span>
                    <span className="uppercase text-muted-foreground">{patch.op ?? "update"}</span>
                    {patch.proposed_by && (
                      <span className="hidden sm:inline text-primary truncate">{patch.proposed_by}</span>
                    )}
                    <span
                      className={`ml-auto shrink-0 border px-2 py-0.5 text-[10px] tracking-wider ${
                        rejected
                          ? "border-destructive/40 bg-destructive/10 text-destructive"
                          : "border-green-500/40 bg-green-500/10 text-green-400"
                      }`}
                    >
                      {(patch.status ?? "applied").toUpperCase()}
                    </span>
                  </button>
                  {isOpen && (
                    <div className="border-t border-border bg-card px-4 py-3 pl-11 text-xs">
                      {rejected && patch.rejection_reason && (
                        <div className="mb-3 border border-destructive/30 bg-destructive/5 p-2 text-destructive">
                          {patch.rejection_reason}
                        </div>
                      )}
                      <div className="pb-1 text-[10px] tracking-widest text-muted-foreground">
                        UPDATED FIELDS{patch.expected_version != null ? ` · EXPECTED v${patch.expected_version}` : ""}
                      </div>
                      {fields.length > 0 ? (
                        <div className="border border-border">
                          {fields.map(([key, val]) => (
                            <div key={key} className="flex border-b border-border last:border-b-0">
                              <span className="w-40 shrink-0 bg-muted/40 px-3 py-1.5 text-muted-foreground">{key}</span>
                              <span className="flex-1 px-3 py-1.5 text-green-400 break-all">{JSON.stringify(val)}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-muted-foreground">No field values recorded.</div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex h-64 flex-col items-center justify-center gap-1 text-muted-foreground font-mono text-sm">
            <span>NO_PATCHES</span>
            <span className="text-xs text-muted-foreground/70">No object mutations were applied in this run.</span>
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
