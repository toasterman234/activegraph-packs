import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { HelpCircle, ExternalLink, X } from "lucide-react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { CONCEPTS, CONCEPTS_INDEX_URL, docsUrl, fetchConceptDoc, type ConceptKey } from "@/lib/concepts";

function DocsSkeleton() {
  return (
    <div className="space-y-2" aria-label="Loading documentation">
      {[80, 95, 70, 90, 60].map((w, i) => (
        <div key={i} className="h-3 bg-muted animate-pulse" style={{ width: `${w}%` }} />
      ))}
    </div>
  );
}

export function ConceptInfo({ concept }: { concept: ConceptKey }) {
  const [open, setOpen] = useState(false);
  const cfg = CONCEPTS[concept];
  const slug = cfg.docsSlug;

  const { data, isLoading, isError } = useQuery({
    queryKey: ["concept-doc", slug],
    queryFn: () => fetchConceptDoc(slug as string),
    enabled: open && !!slug,
    staleTime: Infinity,
    retry: 1,
  });

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label={`About ${cfg.title}`}
        className="inline-flex h-5 w-5 items-center justify-center border border-border text-muted-foreground transition-colors hover:border-primary hover:text-primary"
      >
        <HelpCircle className="h-3 w-3" />
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-2xl gap-0 border-border p-0 font-mono [&>button]:hidden">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <DialogTitle asChild>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-primary" />
                <span className="text-sm font-bold tracking-tight text-primary">
                  CONCEPT · {cfg.title.toUpperCase()}
                </span>
              </div>
            </DialogTitle>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close"
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="max-h-[70vh] overflow-auto px-4 py-4">
            <p className="text-xs leading-relaxed text-muted-foreground">{cfg.blurb}</p>

            {slug && (
              <div className="mt-4">
                {isLoading && <DocsSkeleton />}
                {isError && (
                  <p className="text-xs text-destructive">
                    Couldn't load the docs inline — use the link below to open them.
                  </p>
                )}
                {data && (
                  <div className="concept-docs" dangerouslySetInnerHTML={{ __html: data }} />
                )}
              </div>
            )}

            <a
              href={slug ? docsUrl(slug) : CONCEPTS_INDEX_URL}
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-flex items-center gap-2 border border-primary/40 bg-primary/10 px-3 py-2 text-xs text-primary transition-colors hover:bg-primary/20"
            >
              {slug ? "OPEN IN DOCS" : "BROWSE CONCEPTS"}
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
