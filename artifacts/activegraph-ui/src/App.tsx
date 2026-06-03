import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Layout } from "@/components/layout";
import Dashboard from "@/pages/dashboard";
import Graph from "@/pages/graph";
import Trace from "@/pages/trace";
import Packs from "@/pages/packs";
import Frames from "@/pages/frames";
import Chat from "@/pages/chat";
import NotFound from "@/pages/not-found";

const queryClient = new QueryClient();

function Router() {
  return (
    <Layout>
      <Switch>
        <Route path="/" component={Dashboard} />
        <Route path="/graph" component={Graph} />
        <Route path="/trace" component={Trace} />
        <Route path="/packs" component={Packs} />
        <Route path="/frames" component={Frames} />
        <Route path="/chat" component={Chat} />
        <Route component={NotFound} />
      </Switch>
    </Layout>
  );
}

function App() {
  // Enforce dark mode
  if (typeof document !== "undefined") {
    document.documentElement.classList.add("dark");
  }
  
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <Router />
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
