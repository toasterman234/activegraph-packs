import { useMemo, useState } from "react";
import { ArrowRight } from "lucide-react";
import {
  useGetGraph,
  getGetGraphQueryKey,
  useGetTrace,
  getGetTraceQueryKey,
} from "@workspace/api-client-react";
import { format } from "date-fns";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PageHeader } from "@/components/page-header";

const TRACE_PARAMS = { limit: 500, event_type: "relation.created" } as const;

export default function Relations() {
  const [filter, setFilter] = useState<string | null>(null);

  const { data: graph, isLoading } = useGetGraph(undefined, {
    query: { refetchInterval: 5000, queryKey: getGetGraphQueryKey() },
  });
  const { data: trace } = useGetTrace(TRACE_PARAMS, {
    query: { refetchInterval: 5000, queryKey: getGetTraceQueryKey(TRACE_PARAMS) },
  });

  const createdMap = useMemo(() => {
    const m = new Map<string, string>();
    trace?.events.forEach((e) => {
      const id = (e.payload?.relation as { id?: string } | undefined)?.id ?? e.object_id ?? undefined;
      if (id) m.set(id, e.timestamp);
    });
    return m;
  }, [trace]);

  const relations = graph?.relations ?? [];
  const types = useMemo(() => {
    const c = new Map<string, number>();
    relations.forEach((r) => c.set(r.type, (c.get(r.type) ?? 0) + 1));
    return [...c.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }, [relations]);

  const shown = filter ? relations.filter((r) => r.type === filter) : relations;

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="RELATIONS" concept="relations" subtitle={`${shown.length} EDGES`} />

      <div className="flex flex-1 min-h-0">
        <aside className="hidden lg:flex w-56 shrink-0 flex-col border-r border-border p-3 overflow-auto">
          <div className="px-1 pb-2 text-[10px] tracking-widest text-muted-foreground">FILTER BY TYPE</div>
          <button
            onClick={() => setFilter(null)}
            className={`flex items-center justify-between border-l-2 px-2 py-1.5 text-xs font-mono transition-colors ${
              !filter ? "border-primary bg-primary/10 text-primary" : "border-transparent text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            <span>ALL</span>
            <span className="text-muted-foreground">{relations.length}</span>
          </button>
          {types.map(([type, count]) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`flex items-center justify-between border-l-2 px-2 py-1.5 text-xs font-mono transition-colors ${
                filter === type ? "border-primary bg-primary/10 text-primary" : "border-transparent text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <span className="truncate">{type}</span>
              <span className="text-muted-foreground">{count}</span>
            </button>
          ))}
        </aside>

        <ScrollArea className="flex-1">
          {isLoading && !graph ? (
            <div className="p-4 space-y-2">
              {[1, 2, 3, 4, 5].map((i) => <div key={i} className="h-10 bg-muted animate-pulse border border-border" />)}
            </div>
          ) : shown.length > 0 ? (
            <div className="min-w-[700px]">
              <table className="w-full text-left font-mono text-xs">
                <thead className="sticky top-0 bg-card border-b border-border z-10 text-muted-foreground">
                  <tr>
                    <th className="p-3 font-normal">SOURCE</th>
                    <th className="p-3 font-normal">RELATION</th>
                    <th className="p-3 font-normal">TARGET</th>
                    <th className="p-3 font-normal">CREATED</th>
                  </tr>
                </thead>
                <tbody>
                  {shown.map((r) => {
                    const created = createdMap.get(r.id);
                    return (
                      <tr key={r.id} className="border-b border-border transition-colors hover:bg-muted/50">
                        <td className="p-3 text-foreground">{r.source_id}</td>
                        <td className="p-3">
                          <span className="inline-flex items-center gap-1.5 border border-primary/30 bg-primary/5 px-2 py-0.5 text-primary">
                            <ArrowRight className="h-3 w-3" />
                            {r.type}
                          </span>
                        </td>
                        <td className="p-3 text-foreground">{r.target_id}</td>
                        <td className="p-3 text-muted-foreground">
                          {created ? format(new Date(created), "HH:mm:ss.SSS") : "-"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex h-64 items-center justify-center text-muted-foreground font-mono text-sm">
              {relations.length === 0 ? "NO_RELATIONS" : "NO_RELATIONS_MATCH_FILTER"}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  );
}
