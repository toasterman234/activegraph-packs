import { useState, Fragment } from "react";
import { Shell } from "./_shared/Shell";
import { tools, toolSummary } from "./_shared/data";

export function ToolsPage() {
  const [open, setOpen] = useState<string | null>("t4");

  return (
    <Shell active="tools" title="TOOLS" onInfo={() => {}} subtitle={`${tools.length} CALLS`}>
      <div className="flex h-full">
        <div className="hidden w-56 shrink-0 flex-col border-r border-zinc-800 p-3 lg:flex">
          <div className="px-1 pb-2 text-[10px] tracking-widest text-zinc-500">TOOLS USED</div>
          {toolSummary.map((t) => (
            <div key={t.name} className="flex items-center justify-between px-2 py-1.5 text-xs text-zinc-300">
              <span className="text-cyan-300">{t.name}</span>
              <span className="text-zinc-500">{t.calls}</span>
            </div>
          ))}
        </div>

        <div className="min-w-0 flex-1 overflow-auto">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 border-b border-zinc-800 bg-zinc-950 text-zinc-500">
              <tr>
                <th className="p-3 font-normal">TIME</th>
                <th className="p-3 font-normal">TOOL</th>
                <th className="p-3 font-normal">BEHAVIOR</th>
                <th className="p-3 font-normal">STATUS</th>
                <th className="p-3 font-normal text-right">DURATION</th>
              </tr>
            </thead>
            <tbody>
              {tools.map((t) => {
                const isOpen = open === t.id;
                const err = t.status === "error";
                return (
                  <Fragment key={t.id}>
                    <tr
                      onClick={() => setOpen(isOpen ? null : t.id)}
                      className={`cursor-pointer border-b border-zinc-800 transition-colors ${isOpen ? "bg-cyan-300/5" : "hover:bg-zinc-800/50"}`}
                    >
                      <td className="p-3 text-zinc-500">{t.time}</td>
                      <td className="p-3 text-cyan-300">{t.name}</td>
                      <td className="p-3 text-zinc-300">{t.behavior}</td>
                      <td className="p-3">
                        <span className={`border px-2 py-0.5 text-[10px] tracking-wider ${
                          err ? "border-red-500/40 bg-red-500/10 text-red-400" : "border-green-500/40 bg-green-500/10 text-green-400"
                        }`}>
                          {err ? "ERROR" : "OK"}
                        </span>
                      </td>
                      <td className={`p-3 text-right ${err ? "text-red-400" : "text-zinc-400"}`}>{t.ms}ms</td>
                    </tr>
                    {isOpen && (
                      <tr className="border-b border-zinc-800 bg-zinc-950">
                        <td colSpan={5} className="p-4">
                          <div className="grid gap-3 md:grid-cols-2">
                            <div>
                              <div className="pb-1 text-[10px] tracking-widest text-zinc-500">ARGS</div>
                              <pre className="overflow-x-auto border border-zinc-800 bg-zinc-900/40 p-3 text-[10px] text-zinc-300">{JSON.stringify(t.args, null, 2)}</pre>
                            </div>
                            <div>
                              <div className="pb-1 text-[10px] tracking-widest text-zinc-500">{err ? "ERROR" : "RESULT"}</div>
                              <pre className={`overflow-x-auto border bg-zinc-900/40 p-3 text-[10px] ${err ? "border-red-500/30 text-red-400" : "border-zinc-800 text-zinc-300"}`}>{JSON.stringify(t.result, null, 2)}</pre>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </Shell>
  );
}
