import { Link, useLocation } from "wouter";
import { Activity, Box, ListTree, Package, LayoutDashboard, MessageSquare } from "lucide-react";
import { useHealthCheck } from "@workspace/api-client-react";

export function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();
  const { data: health } = useHealthCheck({ query: { refetchInterval: 10000, queryKey: ["healthCheck"] } });

  const navItems = [
    { href: "/", label: "Dashboard", icon: LayoutDashboard },
    { href: "/graph", label: "Graph", icon: Box },
    { href: "/trace", label: "Trace", icon: Activity },
    { href: "/packs", label: "Packs", icon: Package },
    { href: "/frames", label: "Frames", icon: ListTree },
    { href: "/chat", label: "Chat", icon: MessageSquare },
  ];

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden text-foreground selection:bg-primary selection:text-primary-foreground">
      <aside className="w-64 border-r border-border bg-card flex flex-col">
        <div className="h-14 flex items-center px-4 border-b border-border">
          <div className="font-mono text-sm font-bold tracking-tight text-primary flex items-center gap-2">
            <div className="w-2 h-2 bg-primary animate-pulse" />
            ACTIVEGRAPH
          </div>
        </div>
        
        <nav className="flex-1 py-4 flex flex-col gap-1 px-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location === item.href;
            return (
              <Link key={item.href} href={item.href}>
                <div
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

        <div className="p-4 border-t border-border mt-auto">
          <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
            <div className={`w-2 h-2 rounded-full ${health?.status === 'ok' ? 'bg-green-500' : 'bg-destructive'}`} />
            {health?.status === 'ok' ? 'RUNTIME ONLINE' : 'RUNTIME OFFLINE'}
          </div>
        </div>
      </aside>
      
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <div className="flex-1 overflow-auto bg-background">
          {children}
        </div>
      </main>
    </div>
  );
}
