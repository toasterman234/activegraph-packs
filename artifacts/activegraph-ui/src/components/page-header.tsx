import type { ReactNode } from "react";
import { ConceptInfo } from "@/components/concept-info";
import type { ConceptKey } from "@/lib/concepts";

export function PageHeader({
  title,
  subtitle,
  concept,
}: {
  title: string;
  subtitle?: ReactNode;
  concept?: ConceptKey;
}) {
  return (
    <div className="p-4 border-b border-border flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2">
        <h1 className="text-lg font-mono font-bold">{title}</h1>
        {concept && <ConceptInfo concept={concept} />}
      </div>
      {subtitle != null && (
        <div className="text-xs font-mono text-muted-foreground">{subtitle}</div>
      )}
    </div>
  );
}
