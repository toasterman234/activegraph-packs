import { useGetFrames, getGetFramesQueryKey } from "@workspace/api-client-react";
import { format } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Frames() {
  const { data, isLoading } = useGetFrames({
    query: { refetchInterval: 5000, queryKey: getGetFramesQueryKey() }
  });

  if (isLoading) {
    return <div className="p-6 font-mono text-sm animate-pulse text-muted-foreground">LOADING_FRAMES...</div>;
  }

  return (
    <div className="p-6 max-w-5xl mx-auto w-full">
      <h1 className="text-lg font-mono font-bold mb-6">EXECUTION_FRAMES</h1>
      
      {data?.frames && data.frames.length > 0 ? (
        <div className="space-y-4">
          {data.frames.map(frame => (
            <Card key={frame.id} className="bg-card border-border rounded-none shadow-none">
              <CardHeader className="p-4 border-b border-border bg-background/50">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-mono font-bold flex items-center gap-3">
                    <span className="text-primary">{frame.frame_type || 'SYSTEM'}</span>
                    <span className="text-muted-foreground text-[10px] truncate max-w-[200px]">{frame.id}</span>
                  </CardTitle>
                  <div className="flex gap-4 text-xs font-mono text-muted-foreground">
                    <span>STATUS: {frame.status}</span>
                    <span>EVENTS: {frame.event_count || 0}</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-4">
                <div className="text-xs font-mono text-muted-foreground mb-4 flex gap-6">
                  {frame.started_at && <span>START: {format(new Date(frame.started_at), "HH:mm:ss.SSS")}</span>}
                  {frame.ended_at && <span>END: {format(new Date(frame.ended_at), "HH:mm:ss.SSS")}</span>}
                </div>
                
                {frame.events && frame.events.length > 0 && (
                  <div className="space-y-1">
                    {frame.events.map(event => (
                      <div key={event.id} className="text-[10px] font-mono flex gap-4 p-1 hover:bg-muted">
                        <span className="text-muted-foreground">{format(new Date(event.timestamp), "HH:mm:ss.SSS")}</span>
                        <span className="text-primary w-24 truncate">{event.event_type}</span>
                        <span className="text-muted-foreground w-24 truncate">{event.pack || '-'}</span>
                        <span className="w-32 truncate">{event.behavior_name || '-'}</span>
                        <span className="flex-1 truncate opacity-70">{JSON.stringify(event.payload)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="font-mono text-sm text-muted-foreground">NO_FRAMES_FOUND</div>
      )}
    </div>
  );
}
