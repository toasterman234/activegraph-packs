import { useState, Fragment } from "react";
import { Search, X, ChevronDown } from "lucide-react";
import { Shell } from "./_shared/Shell";
import { traceEvents, eventTypes, packs } from "./_shared/data";

function Dropdown({ label, value, options, onChange }: {
  label: string; value: string | null; options: string[]; onChange: (v: string | null) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-2 border px-2.5 py-1.5 text-xs transition-colors ${
          value ? "border-cyan-300/50 bg-cyan-300/10 text-cyan-300" : "border-zinc-700 text-zinc-400 hover:border-zinc-500"
        }`}
      >
        <span className="text-[10px] tracking-widest text-zinc-500">{label}</span>
        <span>{value ?? "ALL"}</span>
        <ChevronDown className="h-3 w-3" />
      </button>
      {open && (
        <div className="absolute z-20 mt-1 w-48 border border-zinc-700 bg-zinc-900 py-1 text-xs">
          <button onClick={() => { onChange(null); setOpen(false); }} className="block w-full px-3 py-1.5 text-left text-zinc-400 hover:bg-zinc-800">ALL</button>
          {options.map((o) => (
            <button key={o} onClick={() => { onChange(o); setOpen(false); }} className="block w-full px-3 py-1.5 text-left text-zinc-300 hover:bg-zinc-800">{o}</button>
          ))}
        </div>
      )}
    </div>
  );
}

export function TraceFiltered() {
  const [type, setType] = useState<string | null>("behavior.failed");
  const [pack, setPack] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const shown = traceEvents.filter((e) =>
    (!type || e.type === type) && (!pack || e.pack === pack) &&
    (!q || e.object.toLowerCase().includes(q.toLowerCase()))
  );
  const active = [type && `type=${type}`, pack && `pack=${pack}`, q && `object~${q}`].filter(Boolean) as string[];

  return (
    <Shell active="trace" title="EVENT_TRACE" onInfo={() => {}} subtitle={`${shown.length} / ${traceEvents.length} EVENTS`}>
      <div className="flex flex-wrap items-center gap-2 border-b border-zinc-800 p-3">
        <Dropdown label="TYPE" value={type} options={eventTypes} onChange={setType} />
        <Dropdown label="PACK" value={pack} options={packs} onChange={setPack} />
        <div className={`flex items-center gap-2 border px-2.5 py-1.5 ${q ? "border-cyan-300/50" : "border-zinc-700"}`}>
          <Search className="h-3 w-3 text-zinc-500" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="OBJECT…"
            className="w-32 bg-transparent text-xs text-zinc-50 placeholder:text-zinc-600 focus:outline-none"
          />
        </div>
        {active.length > 0 && (
          <button
            onClick={() => { setType(null); setPack(null); setQ(""); }}
            className="flex items-center gap-1 px-2 py-1.5 text-[10px] tracking-widest text-zinc-500 hover:text-red-400"
          >
            <X className="h-3 w-3" /> CLEAR {active.length}
          </button>
        )}
      </div>

      <table className="w-full text-left text-xs">
        <thead className="sticky top-0 border-b border-zinc-800 bg-zinc-950 text-zinc-500">
          <tr>
            <th className="p-3 font-normal">TIMESTAMP</th>
            <th className="p-3 font-normal">TYPE</th>
            <th className="p-3 font-normal">PACK</th>
            <th className="p-3 font-normal">BEHAVIOR</th>
            <th className="p-3 font-normal">OBJECT</th>
          </tr>
        </thead>
        <tbody>
          {shown.map((e) => (
            <tr key={e.id} className="border-b border-zinc-800 transition-colors hover:bg-zinc-800/50">
              <td className="p-3 text-zinc-500">{e.time}</td>
              <td className={`p-3 ${e.type === "behavior.failed" ? "text-red-400" : "text-cyan-300"}`}>{e.type}</td>
              <td className="p-3 text-zinc-300">{e.pack}</td>
              <td className="p-3 text-zinc-300">{e.behavior}</td>
              <td className="p-3 text-zinc-400">{e.object}</td>
            </tr>
          ))}
          {shown.length === 0 && (
            <tr><td colSpan={5} className="p-12 text-center text-zinc-600">NO_EVENTS_MATCH_FILTERS</td></tr>
          )}
        </tbody>
      </table>
    </Shell>
  );
}
