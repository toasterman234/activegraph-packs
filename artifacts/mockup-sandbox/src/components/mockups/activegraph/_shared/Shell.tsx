import {
  Activity, Box, Boxes, ListTree, Package, LayoutDashboard,
  Share2, FileDiff, Wrench, AlertTriangle, HelpCircle,
} from "lucide-react";
import type { ReactNode } from "react";

const nav = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { key: "graph", label: "Graph", icon: Box },
  { key: "objects", label: "Objects", icon: Boxes },
  { key: "trace", label: "Trace", icon: Activity },
  { key: "relations", label: "Relations", icon: Share2, isNew: true },
  { key: "patches", label: "Patches", icon: FileDiff, isNew: true },
  { key: "tools", label: "Tools", icon: Wrench, isNew: true },
  { key: "failures", label: "Failures", icon: AlertTriangle, isNew: true },
  { key: "packs", label: "Packs", icon: Package },
  { key: "frames", label: "Frames", icon: ListTree },
];

export function Shell({
  active, title, subtitle, onInfo, infoActive, children,
}: {
  active: string;
  title: string;
  subtitle?: ReactNode;
  onInfo?: () => void;
  infoActive?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-zinc-950 font-mono text-zinc-50 antialiased selection:bg-cyan-300 selection:text-zinc-950">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950 md:flex">
        <div className="flex h-14 items-center gap-2 border-b border-zinc-800 px-4">
          <div className="h-2 w-2 animate-pulse bg-cyan-300" />
          <span className="text-sm font-bold tracking-tight text-cyan-300">ACTIVEGRAPH</span>
        </div>
        <nav className="flex flex-1 flex-col gap-1 px-2 py-4">
          {nav.map((item) => {
            const Icon = item.icon;
            const isActive = active === item.key;
            return (
              <div
                key={item.key}
                className={`flex items-center gap-3 border-l-2 px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "border-cyan-300 bg-cyan-300/10 text-cyan-300"
                    : "border-transparent text-zinc-400 hover:bg-zinc-800 hover:text-zinc-50"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span className="flex-1">{item.label}</span>
                {item.isNew && !isActive && (
                  <span className="text-[9px] tracking-widest text-cyan-300/70">NEW</span>
                )}
              </div>
            );
          })}
        </nav>
        <div className="mt-auto flex items-center gap-2 border-t border-zinc-800 p-4 text-xs text-zinc-400">
          <div className="h-2 w-2 rounded-full bg-green-500" />
          RUNTIME ONLINE
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-zinc-800 px-4">
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold">{title}</h1>
            {onInfo && (
              <button
                onClick={onInfo}
                aria-label="About this concept"
                className={`flex h-6 w-6 items-center justify-center border transition-colors ${
                  infoActive
                    ? "border-cyan-300 text-cyan-300"
                    : "border-zinc-700 text-zinc-500 hover:border-cyan-300 hover:text-cyan-300"
                }`}
              >
                <HelpCircle className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
          {subtitle && <div className="text-xs text-zinc-400">{subtitle}</div>}
        </div>
        <div className="flex-1 overflow-auto">{children}</div>
      </main>
    </div>
  );
}
