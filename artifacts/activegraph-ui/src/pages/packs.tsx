import { useGetPacks, getGetPacksQueryKey } from "@workspace/api-client-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";

export default function Packs() {
  const { data, isLoading } = useGetPacks({ query: { queryKey: getGetPacksQueryKey() } });

  if (isLoading) {
    return <div className="p-6 font-mono text-sm animate-pulse text-muted-foreground">LOADING_PACKS...</div>;
  }

  return (
    <div className="p-6 max-w-5xl mx-auto w-full">
      <h1 className="text-lg font-mono font-bold mb-6">PACK_REGISTRY</h1>
      
      {data?.packs && data.packs.length > 0 ? (
        <Accordion type="single" collapsible className="space-y-4 font-mono">
          {data.packs.map(pack => (
            <AccordionItem key={pack.name} value={pack.name} className="border border-border bg-card px-4">
              <AccordionTrigger className="hover:no-underline hover:text-primary">
                <div className="flex items-center gap-4">
                  <span className="font-bold">{pack.name}</span>
                  <Badge variant="outline" className="font-mono text-[10px] rounded-none bg-background">{pack.version}</Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent className="pt-4 border-t border-border">
                {pack.description && <p className="mb-6 text-sm text-muted-foreground">{pack.description}</p>}
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                    <h3 className="text-xs font-bold text-primary mb-3">OBJECT_TYPES</h3>
                    <div className="space-y-2">
                      {pack.object_types?.map(ot => (
                        <div key={ot.name} className="p-2 border border-border bg-background/50">
                          <div className="text-xs font-bold">{ot.name}</div>
                          {ot.description && <div className="text-[10px] text-muted-foreground mt-1">{ot.description}</div>}
                        </div>
                      ))}
                      {!pack.object_types?.length && <div className="text-xs text-muted-foreground">NONE</div>}
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-xs font-bold text-primary mb-3">BEHAVIORS</h3>
                    <div className="space-y-2">
                      {pack.behaviors?.map(b => (
                        <div key={b.name} className="p-2 border border-border bg-background/50">
                          <div className="text-xs font-bold">{b.name}</div>
                          <div className="text-[10px] text-muted-foreground mt-1">TRIGGER: {b.trigger || 'manual'}</div>
                          {b.creates && b.creates.length > 0 && (
                            <div className="mt-2 flex gap-1 flex-wrap">
                              {b.creates.map(c => <Badge key={c} variant="outline" className="text-[8px] h-4 rounded-none">{c}</Badge>)}
                            </div>
                          )}
                        </div>
                      ))}
                      {!pack.behaviors?.length && <div className="text-xs text-muted-foreground">NONE</div>}
                    </div>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      ) : (
        <div className="font-mono text-sm text-muted-foreground">NO_PACKS_LOADED</div>
      )}
    </div>
  );
}
