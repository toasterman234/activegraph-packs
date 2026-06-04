import { useState } from "react";
import {
  useGetChatConfig,
  useUpdateChatConfig,
  useListSecrets,
  useSetSecret,
  getGetChatConfigQueryKey,
  getListSecretsQueryKey,
} from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { KeyRound, ShieldCheck, ShieldAlert, Plus, CheckCircle2, Circle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const PROVIDER_KEY_HINTS: Record<string, string> = {
  openai: "OPENAI_API_KEY",
  anthropic: "ANTHROPIC_API_KEY",
};

export default function Secrets() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: config } = useGetChatConfig({
    query: { refetchInterval: 15000, queryKey: getGetChatConfigQueryKey() },
  });
  const { data: secrets } = useListSecrets({
    query: { refetchInterval: 15000, queryKey: getListSecretsQueryKey() },
  });

  const setSecret = useSetSecret();
  const updateConfig = useUpdateChatConfig();

  const [name, setName] = useState("");
  const [value, setValue] = useState("");
  const [providerHint, setProviderHint] = useState("");
  const [model, setModel] = useState("");

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: getGetChatConfigQueryKey() });
    queryClient.invalidateQueries({ queryKey: getListSecretsQueryKey() });
  };

  const handleAddSecret = (e: React.FormEvent) => {
    e.preventDefault();
    const n = name.trim();
    if (!n || !value.trim()) return;
    setSecret.mutate(
      { data: { name: n, value: value.trim(), provider_hint: providerHint.trim() || null } },
      {
        onSuccess: () => {
          toast({ title: `Secret ${n.toUpperCase()} registered` });
          setName("");
          setValue("");
          setProviderHint("");
          refresh();
        },
        onError: () => toast({ title: "Failed to set secret", variant: "destructive" }),
      },
    );
  };

  const quickAdd = (provider: string, keyEnv: string) => {
    setName(keyEnv);
    setProviderHint(provider);
    setValue("");
  };

  const selectProvider = (provider: string) => {
    updateConfig.mutate(
      { data: { provider, model: model.trim() || null } },
      {
        onSuccess: () => {
          toast({ title: `Chat provider set to ${provider}` });
          refresh();
        },
        onError: () => toast({ title: "Failed to update config", variant: "destructive" }),
      },
    );
  };

  const isLive = config?.mode === "live";

  return (
    <div className="h-full flex flex-col bg-background max-w-4xl mx-auto border-x border-border">
      <div className="p-4 border-b border-border bg-card">
        <h1 className="text-lg font-mono font-bold text-primary flex items-center gap-2">
          <KeyRound className="w-5 h-5" />
          SECRETS_&_LLM
        </h1>
        <p className="text-xs font-mono text-muted-foreground">
          Configure the chat LLM. Secret values are used in-process only — never stored in the graph, logs, or disk.
        </p>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-6">
          {/* Current mode banner */}
          <div
            className={`p-4 border font-mono text-sm flex items-start gap-3 ${
              isLive
                ? "border-green-500/40 bg-green-500/5 text-green-400"
                : "border-yellow-500/40 bg-yellow-500/5 text-yellow-400"
            }`}
          >
            {isLive ? <ShieldCheck className="w-5 h-5 shrink-0" /> : <ShieldAlert className="w-5 h-5 shrink-0" />}
            <div className="space-y-1">
              <div className="font-bold uppercase tracking-wide">
                {isLive ? "LIVE LLM" : "MOCK LLM"}
              </div>
              <div className="text-xs text-muted-foreground">
                {isLive ? (
                  <>
                    Chat is using <span className="text-foreground">{config?.provider}</span>
                    {config?.model ? ` (${config.model})` : ""}.
                  </>
                ) : (
                  <>
                    No provider key detected — chat returns canned replies. Add a key below to upgrade automatically.
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Providers */}
          <div className="space-y-2">
            <h2 className="text-xs font-mono font-bold text-muted-foreground uppercase tracking-widest">
              Providers
            </h2>
            <div className="grid gap-2 sm:grid-cols-2">
              {config?.providers?.map((p) => (
                <div
                  key={p.id}
                  className="border border-border bg-card p-3 font-mono text-sm space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-foreground">{p.label}</span>
                    {p.key_present ? (
                      <span className="flex items-center gap-1 text-[10px] text-green-400">
                        <CheckCircle2 className="w-3 h-3" /> KEY SET
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                        <Circle className="w-3 h-3" /> NO KEY
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-muted-foreground">{p.key_env}</div>
                  <div className="flex gap-2">
                    {p.key_present ? (
                      <Button
                        size="sm"
                        variant="outline"
                        className="rounded-none h-7 text-[10px] font-mono flex-1"
                        disabled={updateConfig.isPending || config?.provider === p.id}
                        onClick={() => selectProvider(p.id)}
                      >
                        {config?.provider === p.id ? "ACTIVE" : "USE"}
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        className="rounded-none h-7 text-[10px] font-mono flex-1"
                        onClick={() => quickAdd(p.id, p.key_env)}
                      >
                        ADD KEY
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex gap-2 items-center pt-1">
              <Input
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="MODEL OVERRIDE (optional, e.g. gpt-4o)"
                className="font-mono text-xs rounded-none border-border bg-background h-9"
              />
            </div>
          </div>

          {/* Add secret form */}
          <div className="space-y-2">
            <h2 className="text-xs font-mono font-bold text-muted-foreground uppercase tracking-widest">
              Add Secret
            </h2>
            <form onSubmit={handleAddSecret} className="space-y-2 border border-border bg-card p-3">
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="NAME (e.g. OPENAI_API_KEY)"
                className="font-mono text-sm rounded-none border-border bg-background h-10"
              />
              <Input
                type="password"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="VALUE (never stored)"
                className="font-mono text-sm rounded-none border-border bg-background h-10"
                autoComplete="off"
              />
              <Input
                value={providerHint}
                onChange={(e) => setProviderHint(e.target.value)}
                placeholder="PROVIDER HINT (optional, e.g. openai)"
                className="font-mono text-xs rounded-none border-border bg-background h-9"
              />
              <Button
                type="submit"
                className="rounded-none h-10 w-full bg-primary text-primary-foreground font-mono font-bold hover:bg-primary/90"
                disabled={setSecret.isPending || !name.trim() || !value.trim()}
              >
                <Plus className="w-4 h-4 mr-2" />
                REGISTER
              </Button>
            </form>
            <p className="text-[10px] font-mono text-muted-foreground leading-relaxed">
              You can also set these via environment variables or Replit Secrets. The value is sent once and held in
              process memory only — only the name is recorded in the graph as a credential reference.
            </p>
          </div>

          {/* Registered credential refs */}
          <div className="space-y-2">
            <h2 className="text-xs font-mono font-bold text-muted-foreground uppercase tracking-widest">
              Registered Credentials ({secrets?.total ?? 0})
            </h2>
            {(secrets?.credentials?.length ?? 0) === 0 ? (
              <div className="text-xs font-mono text-muted-foreground border border-border bg-card p-3">
                No credential references registered yet.
              </div>
            ) : (
              <div className="space-y-1">
                {secrets?.credentials?.map((c) => (
                  <div
                    key={c.id ?? c.name}
                    className="flex items-center justify-between border border-border bg-card px-3 py-2 font-mono text-sm"
                  >
                    <div className="flex flex-col">
                      <span className="text-foreground">{c.name}</span>
                      {c.provider_hint && (
                        <span className="text-[10px] text-muted-foreground">{c.provider_hint}</span>
                      )}
                    </div>
                    {c.value_present ? (
                      <span className="flex items-center gap-1 text-[10px] text-green-400">
                        <CheckCircle2 className="w-3 h-3" /> VALUE PRESENT
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[10px] text-yellow-400">
                        <ShieldAlert className="w-3 h-3" /> NAME ONLY
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
