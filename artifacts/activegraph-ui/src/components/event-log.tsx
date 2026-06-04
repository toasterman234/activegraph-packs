import { useState, Fragment } from "react";
import { format } from "date-fns";
import type { TraceEvent } from "@workspace/api-client-react";

export function EventLog({
  events,
  emptyLabel = "NO_EVENTS_LOGGED",
}: {
  events: TraceEvent[];
  emptyLabel?: string;
}) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!events.length) {
    return (
      <div className="flex h-32 items-center justify-center text-muted-foreground font-mono text-sm">
        {emptyLabel}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto border border-border bg-card">
      <table className="w-full text-left font-mono text-xs min-w-[640px]">
        <thead className="bg-card border-b border-border text-muted-foreground">
          <tr>
            <th className="p-3 font-normal">TIMESTAMP</th>
            <th className="p-3 font-normal">TYPE</th>
            <th className="p-3 font-normal">PACK</th>
            <th className="p-3 font-normal">BEHAVIOR</th>
            <th className="p-3 font-normal">OBJECT</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <Fragment key={event.id}>
              <tr
                className={`border-b border-border cursor-pointer transition-colors ${
                  expandedId === event.id ? "bg-primary/5" : "hover:bg-muted/50"
                }`}
                onClick={() => setExpandedId(expandedId === event.id ? null : event.id)}
              >
                <td className="p-3 whitespace-nowrap text-muted-foreground">
                  {format(new Date(event.timestamp), "HH:mm:ss.SSS")}
                </td>
                <td className="p-3 text-primary">{event.event_type}</td>
                <td className="p-3">{event.pack || "-"}</td>
                <td className="p-3">{event.behavior_name || "-"}</td>
                <td className="p-3 truncate max-w-[200px]">{event.object_id || "-"}</td>
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
  );
}
