import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { Shell } from "./_shared/Shell";
import { relations, relationTypes } from "./_shared/data";

export function RelationsPage() {
  const [filter, setFilter] = useState<string | null>(null);
  const shown = filter ? relations.filter((r) => r.type === filter) : relations;

  return (
    <Shell active="relations" title="RELATIONS" onInfo={() => {}} subtitle={`${shown.length} EDGES`}>
      <div className="flex h-full">
        <div className="hidden w-56 shrink-0 flex-col border-r border-zinc-800 p-3 lg:flex">
          <div className="px-1 pb-2 text-[10px] tracking-widest text-zinc-500">FILTER BY TYPE</div>
          <button
            onClick={() => setFilter(null)}
            className={`flex items-center justify-between border-l-2 px-2 py-1.5 text-xs transition-colors ${
              !filter ? "border-cyan-300 bg-cyan-300/10 text-cyan-300" : "border-transparent text-zinc-400 hover:bg-zinc-800"
            }`}
          >
            <span>ALL</span>
            <span className="text-zinc-500">{relations.length}</span>
          </button>
          {relationTypes.map((t) => (
            <button
              key={t.type}
              onClick={() => setFilter(t.type)}
              className={`flex items-center justify-between border-l-2 px-2 py-1.5 text-xs transition-colors ${
                filter === t.type ? "border-cyan-300 bg-cyan-300/10 text-cyan-300" : "border-transparent text-zinc-400 hover:bg-zinc-800"
              }`}
            >
              <span>{t.type}</span>
              <span className="text-zinc-500">{t.count}</span>
            </button>
          ))}
        </div>

        <div className="min-w-0 flex-1 overflow-auto">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 border-b border-zinc-800 bg-zinc-950 text-zinc-500">
              <tr>
                <th className="p-3 font-normal">SOURCE</th>
                <th className="p-3 font-normal">RELATION</th>
                <th className="p-3 font-normal">TARGET</th>
                <th className="p-3 font-normal">CREATED</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((r) => (
                <tr key={r.id} className="border-b border-zinc-800 transition-colors hover:bg-zinc-800/50">
                  <td className="p-3 text-zinc-50">{r.source}</td>
                  <td className="p-3">
                    <span className="inline-flex items-center gap-1.5 border border-cyan-300/30 bg-cyan-300/5 px-2 py-0.5 text-cyan-300">
                      <ArrowRight className="h-3 w-3" />
                      {r.type}
                    </span>
                  </td>
                  <td className="p-3 text-zinc-50">{r.target}</td>
                  <td className="p-3 text-zinc-500">{r.created}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Shell>
  );
}
