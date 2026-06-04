import { useState, useEffect } from "react";
import { Link, useLocation } from "wouter";
import { Activity, Box, Boxes, ListTree, Package, LayoutDashboard, MessageSquare, KeyRound, UserCog, Menu, Share2, FileDiff, Wrench, AlertTriangle } from "lucide-react";
import { useHealthCheck } from "@workspace/api-client-react";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/graph", label: "Graph", icon: Box },
  { href: "/objects", label: "Objects", icon: Boxes },
  { href: "/trace", label: "Trace", icon: Activity },
  { href: "/relations", label: "Relations", icon: Share2 },
  { href: "/patches", label: "Patches", icon: FileDiff },
  { href: "/tools", label: "Tools", icon: Wrench },
  { href: "/failures", label: "Failures", icon: AlertTriangle },
  { href: "/packs", label: "Packs", icon: Package },
  { href: "/frames", label: "Frames", icon: ListTree },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/secrets", label: "Secrets", icon: KeyRound },
  { href: "/identity", label: "Identity", icon: UserCog },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const [location] = useLocation();
  return (
    <nav className="flex-1 py-4 flex flex-col gap-1 px-2">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = location === item.href;
        return (
          <Link key={item.href} href={item.href}>
            <div
              onClick={onNavigate}
              className={`flex items-center gap-3 px-3 py-2 text-sm font-mono cursor-pointer transition-colors ${
                isActive
                  ? "bg-primary/10 text-primary border-l-2 border-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground border-l-2 border-transparent"
              }`}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </div>
          </Link>
        );
      })}
    </nav>
  );
}

function Brand() {
  return (
    <div className="font-mono text-sm font-bold tracking-tight text-primary flex items-center gap-2">
      <div className="w-2 h-2 bg-primary animate-pulse" />
      ACTIVEGRAPH
    </div>
  );
}

export function Layout({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [location] = useLocation();
  const { data: health } = useHealthCheck({ query: { refetchInterval: 10000, queryKey: ["healthCheck"] } });

  useEffect(() => {
    setMobileOpen(false);
  }, [location]);

  const runtimeStatus = (
    <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
      <div className={`w-2 h-2 rounded-full ${health?.status === 'ok' ? 'bg-green-500' : 'bg-destructive'}`} />
      {health?.status === 'ok' ? 'RUNTIME ONLINE' : 'RUNTIME OFFLINE'}
    </div>
  );

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden text-foreground selection:bg-primary selection:text-primary-foreground">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-64 border-r border-border bg-card flex-col">
        <div className="h-14 flex items-center px-4 border-b border-border">
          <Brand />
        </div>
        <NavLinks />
        <div className="p-4 border-t border-border mt-auto">
          {runtimeStatus}
        </div>
      </aside>

      {/* Mobile drawer */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-64 p-0 bg-card border-border flex flex-col">
          <div className="h-14 flex items-center px-4 border-b border-border">
            <SheetTitle asChild>
              <div><Brand /></div>
            </SheetTitle>
          </div>
          <NavLinks onNavigate={() => setMobileOpen(false)} />
          <div className="p-4 border-t border-border mt-auto">
            {runtimeStatus}
          </div>
        </SheetContent>
      </Sheet>

      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Mobile top bar */}
        <div className="md:hidden h-14 flex items-center gap-3 px-4 border-b border-border bg-card shrink-0">
          <button
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation menu"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
          <Brand />
        </div>

        <div className="flex-1 overflow-auto bg-background">
          {children}
        </div>
      </main>
    </div>
  );
}
