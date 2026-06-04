import { useGetTrace, getGetTraceQueryKey } from "@workspace/api-client-react";
import { useState, Fragment } from "react";
import { format } from "date-fns";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function Trace() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  
  const { data: trace, isLoading } = useGetTrace(
    { limit: 100 },
    { query: { 
        refetchInterval: 5000,
        queryKey: getGetTraceQueryKey({ limit: 100 })
      } 
    }
  );

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-border flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-lg font-mono font-bold">EVENT_TRACE</h1>
        <div className="text-xs font-mono text-muted-foreground">
          SHOWING LAST 100 EVENTS
        </div>
      </div>
      
      <ScrollArea className="flex-1">
        {isLoading && !trace ? (
          <div className="p-4 space-y-2">
            {[1,2,3,4,5].map(i => <div key={i} className="h-10 bg-muted animate-pulse border border-border" />)}
          </div>
        ) : trace?.events && trace.events.length > 0 ? (
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
                {trace.events.map(event => (
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
                      <td className="p-3">{event.behavior_name || '-'}</td>
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
            NO_EVENTS_LOGGED
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
