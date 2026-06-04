import { useGetTrace, getGetTraceQueryKey } from "@workspace/api-client-react";
import { useState, useMemo, useRef, useEffect, Fragment } from "react";
import { format } from "date-fns";
import { ChevronDown, X } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PageHeader } from "@/components/page-header";

const TRACE_PARAMS = { limit: 500 } as const;

function TypeDropdown({
  value,
  options,
  onChange,
}: {
  value: string | null;
  options: string[];
  onChange: (v: string | null) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-44 items-center justify-between border border-border bg-card px-2 py-1.5 text-xs font-mono text-foreground transition-colors hover:border-primary/50"
      >
        <span className={value ? "text-primary truncate" : "text-muted-foreground"}>{value ?? "ALL TYPES"}</span>
        <ChevronDown className="h-3 w-3 shrink-0 text-muted-foreground" />
      </button>
      {open && (
        <div className="absolute z-20 mt-1 max-h-72 w-44 overflow-auto border border-border bg-card shadow-lg">
          <button
            onClick={() => { onChange(null); setOpen(false); }}
            className={`block w-full px-2 py-1.5 text-left text-xs font-mono transition-colors hover:bg-muted ${!value ? "text-primary" : "text-muted-foreground"}`}
          >
            ALL TYPES
          </button>
          {options.map((opt) => (
            <button
              key={opt}
              onClick={() => { onChange(opt); setOpen(false); }}
              className={`block w-full px-2 py-1.5 text-left text-xs font-mono transition-colors hover:bg-muted ${value === opt ? "text-primary" : "text-foreground"}`}
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Trace() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [objectQuery, setObjectQuery] = useState("");

  const { data: trace, isLoading } = useGetTrace(TRACE_PARAMS, {
    query: { refetchInterval: 5000, queryKey: getGetTraceQueryKey(TRACE_PARAMS) },
  });

  const events = trace?.events ?? [];

  const typeOptions = useMemo(
    () => [...new Set(events.map((e) => e.event_type))].sort(),
    [events]
  );

  const filtered = useMemo(() => {
    const q = objectQuery.trim().toLowerCase();
    return events.filter((e) => {
      if (typeFilter && e.event_type !== typeFilter) return false;
      if (q && !(e.object_id ?? "").toLowerCase().includes(q)) return false;
      return true;
    });
  }, [events, typeFilter, objectQuery]);

  const hasFilters = typeFilter !== null || objectQuery.trim() !== "";

  return (
    <div className="h-full flex flex-col">
      <PageHeader
        title="EVENT_TRACE"
        concept="events"
        subtitle={hasFilters ? `${filtered.length} / ${events.length} EVENTS` : `LAST ${events.length} EVENTS`}
      />

      <div className="flex flex-wrap items-center gap-2 border-b border-border p-3">
        <TypeDropdown value={typeFilter} options={typeOptions} onChange={setTypeFilter} />
        <input
          value={objectQuery}
          onChange={(e) => setObjectQuery(e.target.value)}
          placeholder="SEARCH OBJECT_ID"
          className="w-56 border border-border bg-card px-2 py-1.5 text-xs font-mono text-foreground placeholder:text-muted-foreground transition-colors focus:border-primary/50 focus:outline-none"
        />
        {hasFilters && (
          <button
            onClick={() => { setTypeFilter(null); setObjectQuery(""); }}
            className="flex items-center gap-1 border border-border px-2 py-1.5 text-xs font-mono text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
          >
            <X className="h-3 w-3" /> CLEAR
          </button>
        )}
      </div>

      <ScrollArea className="flex-1">
        {isLoading && !trace ? (
          <div className="p-4 space-y-2">
            {[1,2,3,4,5].map(i => <div key={i} className="h-10 bg-muted animate-pulse border border-border" />)}
          </div>
        ) : filtered.length > 0 ? (
          <div className="min-w-[800px]">
            <table className="w-full text-left font-mono text-xs">
              <thead className="sticky top-0 bg-card border-b border-border z-10 text-muted-foreground">
                <tr>
                  <th className="p-3 font-normal">TIMESTAMP</th>
                  <th className="p-3 font-normal">TYPE</th>
                  <th className="p-3 font-normal">PACK</th>
                  <th className="p-3 font-normal">BEHAVIOR</th>
                  <th className="p-3 font-normal">OBJECT</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(event => (
                  <Fragment key={event.id}>
                    <tr 
                      className={`border-b border-border cursor-pointer transition-colors ${expandedId === event.id ? 'bg-primary/5' : 'hover:bg-muted/50'}`}
                      onClick={() => setExpandedId(expandedId === event.id ? null : event.id)}
                    >
                      <td className="p-3 whitespace-nowrap text-muted-foreground">
                        {format(new Date(event.timestamp), "HH:mm:ss.SSS")}
                      </td>
                      <td className="p-3 text-primary">{event.event_type}</td>
                      <td className="p-3">{event.pack || '-'}</td>
                      <td className="p-3">{event.behavior_name || (event.payload?.behavior as string | undefined) || '-'}</td>
                      <td className="p-3 truncate max-w-[200px]">{event.object_id || '-'}</td>
                    </tr>
                    {expandedId === event.id && (
                      <tr className="bg-background border-b border-border">
                        <td colSpan={5} className="p-4">
                          <pre className="text-[10px] text-foreground/80 overflow-x-auto p-4 border border-border bg-card">
                            {JSON.stringify(event.payload, null, 2)}
                          </pre>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex h-64 items-center justify-center text-muted-foreground font-mono text-sm">
            {events.length === 0 ? "NO_EVENTS_LOGGED" : "NO_EVENTS_MATCH_FILTER"}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
