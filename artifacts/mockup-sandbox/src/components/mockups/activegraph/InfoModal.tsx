import { ArrowRight, ExternalLink, X } from "lucide-react";
import { Shell } from "./_shared/Shell";
import { relations } from "./_shared/data";

export function InfoModal() {
  return (
    <Shell active="relations" title="RELATIONS" onInfo={() => {}} infoActive subtitle="8 EDGES">
      <div className="relative h-full">
        {/* dimmed page behind the modal */}
        <div className="pointer-events-none select-none opacity-30">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-zinc-800 text-zinc-500">
              <tr><th className="p-3 font-normal">SOURCE</th><th className="p-3 font-normal">RELATION</th><th className="p-3 font-normal">TARGET</th></tr>
            </thead>
            <tbody>
              {relations.slice(0, 6).map((r) => (
                <tr key={r.id} className="border-b border-zinc-800">
                  <td className="p-3 text-zinc-50">{r.source}</td>
                  <td className="p-3 text-cyan-300">{r.type}</td>
                  <td className="p-3 text-zinc-50">{r.target}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="absolute inset-0 flex items-start justify-center bg-zinc-950/70 p-6 pt-12">
          <div className="w-full max-w-lg border border-zinc-700 bg-zinc-950 shadow-2xl">
            <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-cyan-300" />
                <span className="text-sm font-bold tracking-tight text-cyan-300">CONCEPT · RELATIONS</span>
              </div>
              <button className="text-zinc-500 hover:text-zinc-50"><X className="h-4 w-4" /></button>
            </div>

            <div className="space-y-4 px-4 py-4 text-xs leading-relaxed text-zinc-300">
              <p>
                <span className="text-zinc-50">Relations</span> are directed, typed edges between objects in
                the graph. They record how the agent's world connects — which task
                <span className="text-cyan-300"> depends_on</span> another, which agent
                <span className="text-cyan-300"> owns</span> a task, what an object
                <span className="text-cyan-300"> references</span>.
              </p>
              <div className="border border-zinc-800 bg-zinc-900/40 p-3">
                <div className="pb-2 text-[10px] tracking-widest text-zinc-500">ON THIS PAGE</div>
                <ul className="space-y-1.5">
                  {["Every edge as source → type → target", "Filter by relation type in the sidebar", "Created timestamp from the event log"].map((t) => (
                    <li key={t} className="flex items-start gap-2">
                      <ArrowRight className="mt-0.5 h-3 w-3 shrink-0 text-cyan-300" />
                      <span>{t}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <a
                href="https://docs.activegraph.ai/concepts/relations/"
                className="inline-flex items-center gap-2 border border-cyan-300/40 bg-cyan-300/10 px-3 py-2 text-cyan-300 transition-colors hover:bg-cyan-300/20"
              >
                READ THE DOCS
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}
