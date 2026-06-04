import { Link, useParams } from "wouter";
import {
  useGetGraph,
  getGetGraphQueryKey,
  useGetTrace,
  getGetTraceQueryKey,
} from "@workspace/api-client-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ArrowLeft } from "lucide-react";
import { EventLog } from "@/components/event-log";

const TRACE_LIMIT = 500;

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="border border-border bg-background/50 p-3">
      <div className="text-[10px] font-mono text-muted-foreground mb-1">{label}</div>
      <div className="text-xs font-mono break-all">{value || "-"}</div>
    </div>
  );
}

export default function ObjectDetail() {
  const params = useParams<{ id: string }>();
  let id = params.id ?? "";
  try {
    id = decodeURIComponent(id);
  } catch {
    /* keep raw value if malformed */
  }

  const { data: graph, isLoading } = useGetGraph(
    {},
    { query: { queryKey: getGetGraphQueryKey() } }
  );
  const { data: trace } = useGetTrace(
    { limit: TRACE_LIMIT },
    {
      query: {
        refetchInterval: 5000,
        queryKey: getGetTraceQueryKey({ limit: TRACE_LIMIT }),
      },
    }
  );

  const obj = graph?.objects?.find((o) => o.id === id);
  const relations = graph?.relations ?? [];
  const outRel = relations.filter((r) => r.source_id === id);
  const inRel = relations.filter((r) => r.target_id === id);
  const logs = (trace?.events ?? []).filter((e) => e.object_id === id);

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-border flex items-center gap-3">
        <Link href="/objects">
          <div className="text-muted-foreground hover:text-primary cursor-pointer" aria-label="Back to objects">
            <ArrowLeft className="w-4 h-4" />
          </div>
        </Link>
        <div className="min-w-0">
          <h1 className="text-lg font-mono font-bold text-primary truncate">
            {obj ? obj.type : "OBJECT"}
          </h1>
          <div className="text-[10px] font-mono text-muted-foreground truncate">{id}</div>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 max-w-5xl mx-auto w-full space-y-8">
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-muted animate-pulse border border-border" />
              ))}
            </div>
          ) : !obj ? (
            <div className="flex h-32 items-center justify-center text-muted-foreground font-mono text-sm">
              OBJECT_NOT_FOUND
            </div>
          ) : (
            <>
              <section>
                <h2 className="text-xs font-mono font-bold text-primary mb-3">INFO</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Field label="TYPE" value={obj.type} />
                  <Field label="PACK" value={obj.pack} />
                  <Field label="ID" value={obj.id} />
                  <Field label="CREATED_AT" value={obj.created_at} />
                </div>
              </section>

              <section>
                <h2 className="text-xs font-mono font-bold text-primary mb-3">DATA</h2>
                <pre className="text-xs font-mono text-foreground/80 overflow-x-auto p-4 bg-background border border-border">
                  {JSON.stringify(obj.data ?? {}, null, 2)}
                </pre>
              </section>

              <section>
                <h2 className="text-xs font-mono font-bold text-primary mb-3">
                  RELATIONS ({outRel.length + inRel.length})
                </h2>
                {outRel.length + inRel.length === 0 ? (
                  <div className="text-xs font-mono text-muted-foreground">NONE</div>
                ) : (
                  <div className="space-y-2 font-mono">
                    {outRel.map((r) => (
                      <Link key={r.id} href={`/objects/${encodeURIComponent(r.target_id)}`}>
                        <div className="text-xs border border-border p-2 bg-background/50 cursor-pointer hover:border-primary/50">
                          <div className="text-muted-foreground">
                            OUT → <span className="text-primary">{r.type}</span>
                          </div>
                          <div className="truncate mt-1">{r.target_id}</div>
                        </div>
                      </Link>
                    ))}
                    {inRel.map((r) => (
                      <Link key={r.id} href={`/objects/${encodeURIComponent(r.source_id)}`}>
                        <div className="text-xs border border-border p-2 bg-background/50 cursor-pointer hover:border-primary/50">
                          <div className="text-muted-foreground">
                            IN ← <span className="text-primary">{r.type}</span>
                          </div>
                          <div className="truncate mt-1">{r.source_id}</div>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </section>

              <section>
                <h2 className="text-xs font-mono font-bold text-primary mb-1">
                  LOGS ({logs.length})
                </h2>
                <p className="text-[10px] font-mono text-muted-foreground mb-3">
                  FROM LAST {TRACE_LIMIT} TRACE EVENTS
                </p>
                <EventLog events={logs} emptyLabel="NO_EVENTS_FOR_OBJECT" />
              </section>
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
