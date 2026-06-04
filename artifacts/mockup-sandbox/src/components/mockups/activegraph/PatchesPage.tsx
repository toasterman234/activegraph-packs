import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Shell } from "./_shared/Shell";
import { patches } from "./_shared/data";

export function PatchesPage() {
  const [open, setOpen] = useState<string | null>("p1");

  return (
    <Shell active="patches" title="PATCHES" onInfo={() => {}} subtitle="OBJECT MUTATION HISTORY">
      <div className="divide-y divide-zinc-800">
        {patches.map((p) => {
          const isOpen = open === p.id;
          return (
            <div key={p.id}>
              <button
                onClick={() => setOpen(isOpen ? null : p.id)}
                className={`flex w-full items-center gap-3 px-4 py-3 text-left text-xs transition-colors ${
                  isOpen ? "bg-cyan-300/5" : "hover:bg-zinc-800/50"
                }`}
              >
                {isOpen ? <ChevronDown className="h-3.5 w-3.5 text-cyan-300" /> : <ChevronRight className="h-3.5 w-3.5 text-zinc-500" />}
                <span className="w-24 shrink-0 text-zinc-500">{p.time}</span>
                <span className="text-zinc-50">{p.object}</span>
                <span className="text-zinc-600">·</span>
                <span className="text-cyan-300">{p.behavior}</span>
                <span className="ml-auto text-zinc-500">{p.changes.length} FIELD{p.changes.length > 1 ? "S" : ""}</span>
              </button>
              {isOpen && (
                <div className="border-t border-zinc-800 bg-zinc-950 px-4 py-3 pl-11">
                  <div className="border border-zinc-800">
                    {p.changes.map((c) => (
                      <div key={c.field} className="border-b border-zinc-800 last:border-b-0">
                        <div className="bg-zinc-900/60 px-3 py-1 text-[10px] tracking-wider text-zinc-500">{c.field}</div>
                        <div className="flex items-center gap-2 px-3 py-1 text-[11px] text-red-400">
                          <span className="w-4 text-red-500">-</span>
                          <span>{c.from}</span>
                        </div>
                        <div className="flex items-center gap-2 px-3 py-1 text-[11px] text-green-400">
                          <span className="w-4 text-green-500">+</span>
                          <span>{c.to}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Shell>
  );
}
