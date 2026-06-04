import { Link, useParams } from "wouter";
import {
  useGetPacks,
  getGetPacksQueryKey,
  useGetTrace,
  getGetTraceQueryKey,
} from "@workspace/api-client-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
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

export default function BehaviorDetail() {
  const params = useParams<{ name: string }>();
  let name = params.name ?? "";
  try {
    name = decodeURIComponent(name);
  } catch {
    /* keep raw value if malformed */
  }

  const { data: packs, isLoading } = useGetPacks({
    query: { queryKey: getGetPacksQueryKey() },
  });
  const { data: trace } = useGetTrace(
    { limit: TRACE_LIMIT },
    {
      query: {
        refetchInterval: 5000,
        queryKey: getGetTraceQueryKey({ limit: TRACE_LIMIT }),
      },
    }
  );

  let pack: string | undefined;
  let behavior;
  for (const p of packs?.packs ?? []) {
    const match = p.behaviors?.find((b) => b.name === name);
    if (match) {
      pack = p.name;
      behavior = match;
      break;
    }
  }

  const logs = (trace?.events ?? []).filter((e) => e.behavior_name === name);

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-border flex items-center gap-3">
        <Link href="/objects">
          <div className="text-muted-foreground hover:text-primary cursor-pointer" aria-label="Back to behaviors">
            <ArrowLeft className="w-4 h-4" />
          </div>
        </Link>
        <div className="min-w-0">
          <h1 className="text-lg font-mono font-bold text-primary truncate">{name || "BEHAVIOR"}</h1>
          {pack && <div className="text-[10px] font-mono text-muted-foreground truncate">{pack}</div>}
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
          ) : !behavior ? (
            <div className="flex h-32 items-center justify-center text-muted-foreground font-mono text-sm">
              BEHAVIOR_NOT_FOUND
            </div>
          ) : (
            <>
              <section>
                <h2 className="text-xs font-mono font-bold text-primary mb-3">INFO</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Field label="NAME" value={behavior.name} />
                  <Field label="PACK" value={pack} />
                  <Field label="TRIGGER" value={behavior.trigger || "manual"} />
                  <Field
                    label="CREATES"
                    value={
                      behavior.creates && behavior.creates.length > 0 ? (
                        <div className="flex gap-1 flex-wrap">
                          {behavior.creates.map((c) => (
                            <Badge key={c} variant="outline" className="text-[8px] h-4 rounded-none">
                              {c}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        "NONE"
                      )
                    }
                  />
                </div>
                {behavior.description && (
                  <p className="mt-3 text-xs font-mono text-muted-foreground">{behavior.description}</p>
                )}
              </section>

              <section>
                <h2 className="text-xs font-mono font-bold text-primary mb-1">LOGS ({logs.length})</h2>
                <p className="text-[10px] font-mono text-muted-foreground mb-3">
                  FROM LAST {TRACE_LIMIT} TRACE EVENTS
                </p>
                <EventLog events={logs} emptyLabel="NO_EVENTS_FOR_BEHAVIOR" />
              </section>
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
