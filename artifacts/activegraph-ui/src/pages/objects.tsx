import { useState } from "react";
import { Link } from "wouter";
import {
  useGetGraph,
  getGetGraphQueryKey,
  useGetPacks,
  getGetPacksQueryKey,
} from "@workspace/api-client-react";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Search, ChevronRight, Box, Zap } from "lucide-react";

export default function Objects() {
  const [query, setQuery] = useState("");

  const { data: graph, isLoading: graphLoading } = useGetGraph(
    {},
    { query: { queryKey: getGetGraphQueryKey() } }
  );
  const { data: packs, isLoading: packsLoading } = useGetPacks({
    query: { queryKey: getGetPacksQueryKey() },
  });

  const q = query.trim().toLowerCase();

  const objects = (graph?.objects ?? []).filter(
    (o) =>
      !q ||
      o.id.toLowerCase().includes(q) ||
      o.type.toLowerCase().includes(q) ||
      o.pack.toLowerCase().includes(q)
  );

  const behaviors = (packs?.packs ?? [])
    .flatMap((p) => (p.behaviors ?? []).map((b) => ({ ...b, pack: p.name })))
    .filter(
      (b) =>
        !q ||
        b.name.toLowerCase().includes(q) ||
        b.pack.toLowerCase().includes(q) ||
        (b.trigger ?? "").toLowerCase().includes(q)
    );

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-border flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-lg font-mono font-bold whitespace-nowrap">OBJECTS_&amp;_BEHAVIORS</h1>
        <div className="relative w-full sm:max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Filter by name, type, pack..."
            className="pl-9 font-mono text-xs h-9 bg-background/50"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </div>

      <Tabs defaultValue="objects" className="flex-1 flex flex-col min-h-0">
        <div className="px-4 pt-4">
          <TabsList className="font-mono rounded-none">
            <TabsTrigger value="objects" className="rounded-none font-mono text-xs gap-2">
              <Box className="w-3.5 h-3.5" /> OBJECTS
              <Badge variant="outline" className="rounded-none text-[10px] h-4 bg-background">
                {objects.length}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="behaviors" className="rounded-none font-mono text-xs gap-2">
              <Zap className="w-3.5 h-3.5" /> BEHAVIORS
              <Badge variant="outline" className="rounded-none text-[10px] h-4 bg-background">
                {behaviors.length}
              </Badge>
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="objects" className="flex-1 min-h-0 mt-0">
          <ScrollArea className="h-full p-4">
            {graphLoading ? (
              <div className="space-y-2">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-14 bg-muted animate-pulse border border-border" />
                ))}
              </div>
            ) : objects.length > 0 ? (
              <div className="space-y-2">
                {objects.map((obj) => (
                  <Link key={obj.id} href={`/objects/${encodeURIComponent(obj.id)}`}>
                    <div className="group flex items-center justify-between gap-4 border border-border bg-card p-3 cursor-pointer hover:border-primary/50 transition-colors">
                      <div className="min-w-0">
                        <div className="text-[10px] font-mono text-muted-foreground mb-1">{obj.pack}</div>
                        <div className="text-sm font-mono font-bold text-primary truncate">{obj.type}</div>
                        <div className="text-[10px] font-mono text-muted-foreground truncate mt-1">{obj.id}</div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary shrink-0" />
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="flex h-32 items-center justify-center text-muted-foreground font-mono text-sm">
                NO_OBJECTS_FOUND
              </div>
            )}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="behaviors" className="flex-1 min-h-0 mt-0">
          <ScrollArea className="h-full p-4">
            {packsLoading ? (
              <div className="space-y-2">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-14 bg-muted animate-pulse border border-border" />
                ))}
              </div>
            ) : behaviors.length > 0 ? (
              <div className="space-y-2">
                {behaviors.map((b) => (
                  <Link key={`${b.pack}/${b.name}`} href={`/behaviors/${encodeURIComponent(b.name)}`}>
                    <div className="group flex items-center justify-between gap-4 border border-border bg-card p-3 cursor-pointer hover:border-primary/50 transition-colors">
                      <div className="min-w-0">
                        <div className="text-[10px] font-mono text-muted-foreground mb-1">{b.pack}</div>
                        <div className="text-sm font-mono font-bold text-primary truncate">{b.name}</div>
                        <div className="text-[10px] font-mono text-muted-foreground truncate mt-1">
                          TRIGGER: {b.trigger || "manual"}
                        </div>
                        {b.creates && b.creates.length > 0 && (
                          <div className="mt-2 flex gap-1 flex-wrap">
                            {b.creates.map((c) => (
                              <Badge key={c} variant="outline" className="text-[8px] h-4 rounded-none">
                                {c}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                      <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary shrink-0" />
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="flex h-32 items-center justify-center text-muted-foreground font-mono text-sm">
                NO_BEHAVIORS_FOUND
              </div>
            )}
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}
