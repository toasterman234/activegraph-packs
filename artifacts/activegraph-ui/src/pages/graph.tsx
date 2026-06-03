import { useGetGraph, getGetGraphQueryKey } from "@workspace/api-client-react";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function Graph() {
  const [packFilter, setPackFilter] = useState("");
  const { data: graph, isLoading } = useGetGraph(
    { pack: packFilter || undefined },
    { query: { queryKey: getGetGraphQueryKey({ pack: packFilter || undefined }) } }
  );

  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selectedObject = graph?.objects?.find(o => o.id === selectedId);

  return (
    <div className="h-full flex flex-col md:flex-row overflow-hidden">
      <div className="flex-1 flex flex-col border-r border-border h-full">
        <div className="p-4 border-b border-border flex items-center gap-4">
          <h1 className="text-lg font-mono font-bold whitespace-nowrap">GRAPH_EXPLORER</h1>
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Filter by pack..."
              className="pl-9 font-mono text-xs h-9 bg-background/50"
              value={packFilter}
              onChange={(e) => setPackFilter(e.target.value)}
            />
          </div>
        </div>
        
        <ScrollArea className="flex-1 p-4">
          {isLoading ? (
            <div className="space-y-2">
              {[1,2,3].map(i => <div key={i} className="h-16 bg-muted animate-pulse border border-border" />)}
            </div>
          ) : graph?.objects && graph.objects.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {graph.objects.map(obj => (
                <div 
                  key={obj.id}
                  onClick={() => setSelectedId(obj.id)}
                  className={`border p-3 cursor-pointer transition-colors ${selectedId === obj.id ? 'border-primary bg-primary/5' : 'border-border bg-card hover:border-primary/50'}`}
                >
                  <div className="text-[10px] font-mono text-muted-foreground mb-1">{obj.pack}</div>
                  <div className="text-sm font-mono font-bold truncate text-primary">{obj.type}</div>
                  <div className="text-[10px] font-mono mt-2 truncate text-muted-foreground">{obj.id}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground font-mono text-sm">
              NO_OBJECTS_FOUND
            </div>
          )}
        </ScrollArea>
      </div>

      {selectedObject && (
        <div className="w-full md:w-96 flex flex-col h-full bg-card border-l border-border">
          <div className="p-4 border-b border-border">
            <h2 className="text-sm font-mono font-bold text-primary truncate">INSPECT: {selectedObject.type}</h2>
            <div className="text-[10px] font-mono text-muted-foreground truncate">{selectedObject.id}</div>
          </div>
          <ScrollArea className="flex-1 p-4">
            <pre className="text-xs font-mono text-foreground/80 overflow-x-auto p-4 bg-background border border-border">
              {JSON.stringify(selectedObject.data, null, 2)}
            </pre>
            
            {graph?.relations && graph.relations.some(r => r.source_id === selectedObject.id || r.target_id === selectedObject.id) && (
              <div className="mt-6">
                <h3 className="text-xs font-mono font-bold mb-3">RELATIONS</h3>
                <div className="space-y-2">
                  {graph.relations.filter(r => r.source_id === selectedObject.id).map(r => (
                    <div key={r.id} className="text-xs font-mono border border-border p-2 bg-background/50">
                      <div className="text-muted-foreground">OUT → <span className="text-primary">{r.type}</span></div>
                      <div className="truncate mt-1">{r.target_id}</div>
                    </div>
                  ))}
                  {graph.relations.filter(r => r.target_id === selectedObject.id).map(r => (
                    <div key={r.id} className="text-xs font-mono border border-border p-2 bg-background/50">
                      <div className="text-muted-foreground">IN ← <span className="text-primary">{r.type}</span></div>
                      <div className="truncate mt-1">{r.source_id}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </ScrollArea>
        </div>
      )}
    </div>
  );
}
