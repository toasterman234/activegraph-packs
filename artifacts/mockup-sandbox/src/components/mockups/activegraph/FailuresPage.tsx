import { useState, Fragment } from "react";
import { AlertTriangle } from "lucide-react";
import { Shell } from "./_shared/Shell";
import { failures, failureReasons } from "./_shared/data";

export function FailuresPage() {
  const [filter, setFilter] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>("f1");
  const shown = filter ? failures.filter((f) => f.reason === filter) : failures;

  return (
    <Shell active="failures" title="FAILURES" onInfo={() => {}} subtitle={`${failures.length} IN LAST RUN`}>
      <div className="grid grid-cols-2 gap-px border-b border-zinc-800 bg-zinc-800 sm:grid-cols-5">
        <button
          onClick={() => setFilter(null)}
          className={`bg-zinc-950 p-4 text-left transition-colors hover:bg-zinc-900 ${!filter ? "ring-1 ring-inset ring-cyan-300" : ""}`}
        >
          <div className="text-2xl font-bold text-zinc-50">{failures.length}</div>
          <div className="text-[10px] tracking-widest text-zinc-500">TOTAL</div>
        </button>
        {failureReasons.map((r) => (
          <button
            key={r.reason}
            onClick={() => setFilter(r.reason)}
            className={`bg-zinc-950 p-4 text-left transition-colors hover:bg-zinc-900 ${filter === r.reason ? "ring-1 ring-inset ring-cyan-300" : ""}`}
          >
            <div className="text-2xl font-bold text-red-400">{r.count}</div>
            <div className="text-[10px] tracking-widest text-zinc-500">{r.reason}</div>
          </button>
        ))}
      </div>

      <table className="w-full text-left text-xs">
        <thead className="border-b border-zinc-800 text-zinc-500">
          <tr>
            <th className="p-3 font-normal">TIME</th>
            <th className="p-3 font-normal">REASON</th>
            <th className="p-3 font-normal">SUBJECT</th>
            <th className="p-3 font-normal">MESSAGE</th>
          </tr>
        </thead>
        <tbody>
          {shown.map((f) => {
            const isOpen = open === f.id;
            return (
              <Fragment key={f.id}>
                <tr
                  onClick={() => setOpen(isOpen ? null : f.id)}
                  className={`cursor-pointer border-b border-zinc-800 transition-colors ${isOpen ? "bg-red-500/5" : "hover:bg-zinc-800/50"}`}
                >
                  <td className="p-3 align-top text-zinc-500">{f.time}</td>
                  <td className="p-3 align-top">
                    <span className="inline-flex items-center gap-1.5 border border-red-500/40 bg-red-500/10 px-2 py-0.5 text-red-400">
                      <AlertTriangle className="h-3 w-3" />
                      {f.reason}
                    </span>
                  </td>
                  <td className="p-3 align-top">
                    <span className="text-zinc-50">{f.subject}</span>
                    <span className="ml-1 text-[10px] text-zinc-600">[{f.kind}]</span>
                  </td>
                  <td className="max-w-[420px] truncate p-3 align-top text-zinc-400">{f.message}</td>
                </tr>
                {isOpen && (
                  <tr className="border-b border-zinc-800 bg-zinc-950">
                    <td colSpan={4} className="p-4">
                      <pre className="overflow-x-auto border border-red-500/30 bg-zinc-900/40 p-3 text-[10px] text-red-400">{f.message}</pre>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </Shell>
  );
}
