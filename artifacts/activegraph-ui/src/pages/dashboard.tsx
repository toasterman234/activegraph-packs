import { useGetSummary, useResetRuntime, getGetSummaryQueryKey, getGetTraceQueryKey, getGetGraphQueryKey, getGetPacksQueryKey, getGetFramesQueryKey } from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw, Box, Activity, Package, ListTree, Link as LinkIcon } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function Dashboard() {
  const { data: summary, isLoading } = useGetSummary({
    query: {
      refetchInterval: 3000,
      queryKey: getGetSummaryQueryKey()
    }
  });
  
  const resetRuntime = useResetRuntime();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const handleReset = () => {
    resetRuntime.mutate(undefined, {
      onSuccess: () => {
        toast({ title: "Runtime reset successful" });
        queryClient.invalidateQueries({ queryKey: getGetSummaryQueryKey() });
        queryClient.invalidateQueries({ queryKey: getGetTraceQueryKey() });
        queryClient.invalidateQueries({ queryKey: getGetGraphQueryKey() });
        queryClient.invalidateQueries({ queryKey: getGetPacksQueryKey() });
        queryClient.invalidateQueries({ queryKey: getGetFramesQueryKey() });
      },
      onError: () => {
        toast({ title: "Failed to reset runtime", variant: "destructive" });
      }
    });
  };

  if (isLoading && !summary) {
    return (
      <div className="p-6">
        <div className="animate-pulse bg-muted h-8 w-48 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="animate-pulse bg-card border border-border h-24" />
          ))}
        </div>
      </div>
    );
  }

  const stats = [
    { label: "OBJECTS", value: summary?.object_count ?? 0, icon: Box },
    { label: "RELATIONS", value: summary?.relation_count ?? 0, icon: LinkIcon },
    { label: "EVENTS", value: summary?.event_count ?? 0, icon: Activity },
    { label: "FRAMES", value: summary?.frame_count ?? 0, icon: ListTree },
  ];

  return (
    <div className="p-4 sm:p-6 flex flex-col gap-6 max-w-6xl mx-auto w-full">
      <div className="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center">
        <div>
          <h1 className="text-xl sm:text-2xl font-mono font-bold">SYSTEM_DASHBOARD</h1>
          <p className="text-sm font-mono text-muted-foreground mt-1 text-[10px] uppercase tracking-wider">
            RUNTIME STATUS: {summary?.runtime_ready ? 'READY' : 'INITIALIZING'}
          </p>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={handleReset} 
          disabled={resetRuntime.isPending}
          className="font-mono text-xs font-bold uppercase"
        >
          <RefreshCw className={`w-3 h-3 mr-2 ${resetRuntime.isPending ? 'animate-spin' : ''}`} />
          Reset Runtime
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <Card key={i} className="bg-card/50 backdrop-blur border-border/50">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-mono font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-mono">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {summary?.by_type && summary.by_type.length > 0 && (
        <Card className="bg-card/50 backdrop-blur border-border/50">
          <CardHeader>
            <CardTitle className="text-xs font-mono font-medium text-muted-foreground">OBJECTS BY TYPE</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {summary.by_type.map((item, i) => (
                <div key={i} className="flex items-center">
                  <div className="w-full flex-1">
                    <div className="flex justify-between mb-1">
                      <span className="text-xs font-mono">{item.pack} / {item.type}</span>
                      <span className="text-xs font-mono font-bold text-primary">{item.count}</span>
                    </div>
                    <div className="h-1 w-full bg-muted overflow-hidden">
                      <div 
                        className="h-full bg-primary" 
                        style={{ width: `${Math.min(100, (item.count / summary.object_count) * 100)}%` }} 
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
