import { useEffect, useState } from "react";
import {
  useGetProfile,
  useUpdateProfile,
  useSeedProfile,
  useUpdatePersonality,
  useSaveGoal,
  useDeleteGoal,
  useSaveInstruction,
  useDeleteInstruction,
  getGetProfileQueryKey,
} from "@workspace/api-client-react";
import type {
  ProfileInfo,
  GoalInfo,
  InstructionInfo,
} from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  UserCog,
  Save,
  Plus,
  Trash2,
  Pencil,
  X,
  Target,
  ScrollText,
  Sparkles,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const TONES = ["neutral", "warm", "direct", "formal", "casual", "technical"];
const VERBOSITIES = ["concise", "balanced", "detailed"];
const FORMALITIES = ["informal", "neutral", "formal"];
const GOAL_PRIORITIES = ["low", "medium", "high", "critical"];
const GOAL_STATUSES = ["active", "paused", "completed", "cancelled"];

const selectCls =
  "font-mono text-xs rounded-none border border-border bg-background h-9 px-2 text-foreground focus-visible:outline-none focus-visible:border-primary";

const labelCls =
  "text-[10px] font-mono font-bold text-muted-foreground uppercase tracking-widest";

const sectionTitleCls =
  "text-xs font-mono font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2";

export default function Identity() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: profile } = useGetProfile({
    query: { refetchInterval: 20000, queryKey: getGetProfileQueryKey() },
  });

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: getGetProfileQueryKey() });

  const seedProfile = useSeedProfile();

  const handleSeed = () => {
    seedProfile.mutate(undefined, {
      onSuccess: () => {
        toast({ title: "Default profile created" });
        refresh();
      },
      onError: () => toast({ title: "Failed to create profile", variant: "destructive" }),
    });
  };

  return (
    <div className="h-full flex flex-col bg-background max-w-4xl mx-auto border-x border-border">
      <div className="p-4 border-b border-border bg-card">
        <h1 className="text-lg font-mono font-bold text-primary flex items-center gap-2">
          <UserCog className="w-5 h-5" />
          IDENTITY_&_PROFILE
        </h1>
        <p className="text-xs font-mono text-muted-foreground">
          The assistant's self-knowledge. Edits write straight to the agent_profile graph objects.
        </p>
      </div>

      <ScrollArea className="flex-1 p-4">
        {!profile ? (
          <div className="text-xs font-mono text-muted-foreground border border-border bg-card p-3">
            Loading profile…
          </div>
        ) : !profile.exists || !profile.profile ? (
          <EmptyState onSeed={handleSeed} pending={seedProfile.isPending} />
        ) : (
          <div className="space-y-8">
            <ProfileSection profile={profile.profile} onSaved={refresh} />
            <PersonalitySection
              personality={profile.personality}
              onSaved={refresh}
            />
            <GoalsSection goals={profile.goals} onSaved={refresh} />
            <InstructionsSection instructions={profile.instructions} onSaved={refresh} />
          </div>
        )}
      </ScrollArea>
    </div>
  );
}

function EmptyState({ onSeed, pending }: { onSeed: () => void; pending: boolean }) {
  return (
    <div className="border border-border bg-card p-6 font-mono text-sm space-y-4 text-center">
      <Sparkles className="w-8 h-8 mx-auto text-primary" />
      <div className="space-y-1">
        <div className="font-bold text-foreground uppercase tracking-wide">No profile yet</div>
        <p className="text-xs text-muted-foreground max-w-md mx-auto">
          The assistant has no identity loaded. Create the seeded default profile to give it a
          name, mission, and personality you can edit.
        </p>
      </div>
      <Button
        className="rounded-none h-10 bg-primary text-primary-foreground font-mono font-bold hover:bg-primary/90"
        disabled={pending}
        onClick={onSeed}
      >
        <Plus className="w-4 h-4 mr-2" />
        CREATE DEFAULT PROFILE
      </Button>
    </div>
  );
}

function ProfileSection({ profile, onSaved }: { profile: ProfileInfo; onSaved: () => void }) {
  const { toast } = useToast();
  const updateProfile = useUpdateProfile();

  const [name, setName] = useState(profile.name ?? "");
  const [mission, setMission] = useState(profile.mission ?? "");
  const [personalityDesc, setPersonalityDesc] = useState(
    profile.personality_description ?? "",
  );
  const [ownerName, setOwnerName] = useState(profile.owner_name ?? "");

  useEffect(() => {
    setName(profile.name ?? "");
    setMission(profile.mission ?? "");
    setPersonalityDesc(profile.personality_description ?? "");
    setOwnerName(profile.owner_name ?? "");
  }, [profile.id, profile.name, profile.mission, profile.personality_description, profile.owner_name]);

  const save = () => {
    if (!name.trim()) {
      toast({ title: "Name cannot be empty", variant: "destructive" });
      return;
    }
    updateProfile.mutate(
      {
        data: {
          name: name.trim(),
          mission,
          personality_description: personalityDesc,
          owner_name: ownerName.trim() || null,
        },
      },
      {
        onSuccess: () => {
          toast({ title: "Profile updated" });
          onSaved();
        },
        onError: () => toast({ title: "Failed to update profile", variant: "destructive" }),
      },
    );
  };

  return (
    <section className="space-y-3">
      <h2 className={sectionTitleCls}>
        <UserCog className="w-3.5 h-3.5" /> Profile
      </h2>
      <div className="border border-border bg-card p-3 space-y-3">
        <div className="space-y-1">
          <label className={labelCls}>Name</label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Assistant name"
            className="font-mono text-sm rounded-none border-border bg-background h-10"
          />
        </div>
        <div className="space-y-1">
          <label className={labelCls}>Owner Name</label>
          <Input
            value={ownerName}
            onChange={(e) => setOwnerName(e.target.value)}
            placeholder="Who this assistant serves (optional)"
            className="font-mono text-sm rounded-none border-border bg-background h-10"
          />
        </div>
        <div className="space-y-1">
          <label className={labelCls}>Mission</label>
          <Textarea
            value={mission}
            onChange={(e) => setMission(e.target.value)}
            placeholder="Mission statement (1–3 sentences)"
            className="font-mono text-sm rounded-none border-border bg-background min-h-[72px]"
          />
        </div>
        <div className="space-y-1">
          <label className={labelCls}>Personality Description</label>
          <Textarea
            value={personalityDesc}
            onChange={(e) => setPersonalityDesc(e.target.value)}
            placeholder="Free-text personality, e.g. 'Direct, analytical, candid.'"
            className="font-mono text-sm rounded-none border-border bg-background min-h-[72px]"
          />
        </div>
        <Button
          className="rounded-none h-10 w-full bg-primary text-primary-foreground font-mono font-bold hover:bg-primary/90"
          disabled={updateProfile.isPending || !name.trim()}
          onClick={save}
        >
          <Save className="w-4 h-4 mr-2" />
          SAVE PROFILE
        </Button>
      </div>
    </section>
  );
}

function PersonalitySection({
  personality,
  onSaved,
}: {
  personality?: { tone: string; verbosity: string; formality: string };
  onSaved: () => void;
}) {
  const { toast } = useToast();
  const updatePersonality = useUpdatePersonality();

  const [tone, setTone] = useState(personality?.tone ?? "neutral");
  const [verbosity, setVerbosity] = useState(personality?.verbosity ?? "balanced");
  const [formality, setFormality] = useState(personality?.formality ?? "neutral");

  useEffect(() => {
    setTone(personality?.tone ?? "neutral");
    setVerbosity(personality?.verbosity ?? "balanced");
    setFormality(personality?.formality ?? "neutral");
  }, [personality?.tone, personality?.verbosity, personality?.formality]);

  const save = () => {
    updatePersonality.mutate(
      { data: { tone, verbosity, formality } },
      {
        onSuccess: () => {
          toast({ title: "Personality updated" });
          onSaved();
        },
        onError: () => toast({ title: "Failed to update personality", variant: "destructive" }),
      },
    );
  };

  return (
    <section className="space-y-3">
      <h2 className={sectionTitleCls}>
        <Sparkles className="w-3.5 h-3.5" /> Personality
      </h2>
      <div className="border border-border bg-card p-3 space-y-3">
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="space-y-1 flex flex-col">
            <label className={labelCls}>Tone</label>
            <select value={tone} onChange={(e) => setTone(e.target.value)} className={selectCls}>
              {TONES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1 flex flex-col">
            <label className={labelCls}>Verbosity</label>
            <select
              value={verbosity}
              onChange={(e) => setVerbosity(e.target.value)}
              className={selectCls}
            >
              {VERBOSITIES.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1 flex flex-col">
            <label className={labelCls}>Formality</label>
            <select
              value={formality}
              onChange={(e) => setFormality(e.target.value)}
              className={selectCls}
            >
              {FORMALITIES.map((f) => (
                <option key={f} value={f}>{f}</option>
              ))}
            </select>
          </div>
        </div>
        <Button
          variant="outline"
          className="rounded-none h-9 text-[10px] font-mono"
          disabled={updatePersonality.isPending}
          onClick={save}
        >
          <Save className="w-3.5 h-3.5 mr-2" />
          SAVE PERSONALITY
        </Button>
      </div>
    </section>
  );
}

const emptyGoal = { text: "", priority: "medium", status: "active", domain: "" };

function GoalsSection({ goals, onSaved }: { goals: GoalInfo[]; onSaved: () => void }) {
  const { toast } = useToast();
  const saveGoal = useSaveGoal();
  const deleteGoal = useDeleteGoal();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({ ...emptyGoal });

  const reset = () => {
    setEditingId(null);
    setForm({ ...emptyGoal });
  };

  const startEdit = (g: GoalInfo) => {
    setEditingId(g.id);
    setForm({
      text: g.text ?? "",
      priority: g.priority ?? "medium",
      status: g.status ?? "active",
      domain: g.domain ?? "",
    });
  };

  const save = () => {
    if (!form.text.trim()) {
      toast({ title: "Goal text is required", variant: "destructive" });
      return;
    }
    saveGoal.mutate(
      {
        data: {
          id: editingId,
          text: form.text.trim(),
          priority: form.priority,
          status: form.status,
          domain: form.domain.trim() || null,
        },
      },
      {
        onSuccess: () => {
          toast({ title: editingId ? "Goal updated" : "Goal added" });
          reset();
          onSaved();
        },
        onError: () => toast({ title: "Failed to save goal", variant: "destructive" }),
      },
    );
  };

  const remove = (id: string) => {
    deleteGoal.mutate(
      { data: { id } },
      {
        onSuccess: () => {
          toast({ title: "Goal deleted" });
          if (editingId === id) reset();
          onSaved();
        },
        onError: () => toast({ title: "Failed to delete goal", variant: "destructive" }),
      },
    );
  };

  return (
    <section className="space-y-3">
      <h2 className={sectionTitleCls}>
        <Target className="w-3.5 h-3.5" /> Goals ({goals.length})
      </h2>

      <div className="space-y-1">
        {goals.length === 0 ? (
          <div className="text-xs font-mono text-muted-foreground border border-border bg-card p-3">
            No goals defined yet.
          </div>
        ) : (
          goals.map((g) => (
            <div
              key={g.id}
              className="flex items-start justify-between gap-3 border border-border bg-card px-3 py-2 font-mono text-sm"
            >
              <div className="flex flex-col gap-1 min-w-0">
                <span className="text-foreground break-words">{g.text}</span>
                <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
                  {g.priority} · {g.status}
                  {g.domain ? ` · ${g.domain}` : ""}
                </span>
              </div>
              <div className="flex gap-1 shrink-0">
                <button
                  onClick={() => startEdit(g)}
                  className="text-muted-foreground hover:text-primary p-1"
                  aria-label="Edit goal"
                >
                  <Pencil className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => remove(g.id)}
                  className="text-muted-foreground hover:text-destructive p-1"
                  aria-label="Delete goal"
                  disabled={deleteGoal.isPending}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="border border-border bg-card p-3 space-y-3">
        <div className="flex items-center justify-between">
          <span className={labelCls}>{editingId ? "Edit Goal" : "Add Goal"}</span>
          {editingId && (
            <button
              onClick={reset}
              className="text-[10px] font-mono text-muted-foreground hover:text-foreground flex items-center gap-1"
            >
              <X className="w-3 h-3" /> CANCEL
            </button>
          )}
        </div>
        <Textarea
          value={form.text}
          onChange={(e) => setForm({ ...form, text: e.target.value })}
          placeholder="Goal statement (one clear sentence)"
          className="font-mono text-sm rounded-none border-border bg-background min-h-[60px]"
        />
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="space-y-1 flex flex-col">
            <label className={labelCls}>Priority</label>
            <select
              value={form.priority}
              onChange={(e) => setForm({ ...form, priority: e.target.value })}
              className={selectCls}
            >
              {GOAL_PRIORITIES.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1 flex flex-col">
            <label className={labelCls}>Status</label>
            <select
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
              className={selectCls}
            >
              {GOAL_STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1 flex flex-col">
            <label className={labelCls}>Domain</label>
            <Input
              value={form.domain}
              onChange={(e) => setForm({ ...form, domain: e.target.value })}
              placeholder="optional"
              className="font-mono text-xs rounded-none border-border bg-background h-9"
            />
          </div>
        </div>
        <Button
          className="rounded-none h-9 text-[10px] font-mono bg-primary text-primary-foreground font-bold hover:bg-primary/90"
          disabled={saveGoal.isPending || !form.text.trim()}
          onClick={save}
        >
          <Plus className="w-3.5 h-3.5 mr-2" />
          {editingId ? "UPDATE GOAL" : "ADD GOAL"}
        </Button>
      </div>
    </section>
  );
}

const emptyInstr = {
  text: "",
  scope: "global",
  priority: 50,
  active: true,
  applies_to_channel: "",
  applies_to_audience_role: "",
};

function InstructionsSection({
  instructions,
  onSaved,
}: {
  instructions: InstructionInfo[];
  onSaved: () => void;
}) {
  const { toast } = useToast();
  const saveInstruction = useSaveInstruction();
  const deleteInstruction = useDeleteInstruction();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({ ...emptyInstr });

  const reset = () => {
    setEditingId(null);
    setForm({ ...emptyInstr });
  };

  const startEdit = (i: InstructionInfo) => {
    setEditingId(i.id);
    setForm({
      text: i.text ?? "",
      scope: i.scope ?? "global",
      priority: i.priority ?? 50,
      active: i.active ?? true,
      applies_to_channel: i.applies_to_channel ?? "",
      applies_to_audience_role: i.applies_to_audience_role ?? "",
    });
  };

  const save = () => {
    if (!form.text.trim()) {
      toast({ title: "Instruction text is required", variant: "destructive" });
      return;
    }
    const priority = Math.max(0, Math.min(100, Number(form.priority) || 0));
    saveInstruction.mutate(
      {
        data: {
          id: editingId,
          text: form.text.trim(),
          scope: form.scope.trim() || "global",
          priority,
          active: form.active,
          applies_to_channel: form.applies_to_channel.trim() || null,
          applies_to_audience_role: form.applies_to_audience_role.trim() || null,
        },
      },
      {
        onSuccess: () => {
          toast({ title: editingId ? "Instruction updated" : "Instruction added" });
          reset();
          onSaved();
        },
        onError: () => toast({ title: "Failed to save instruction", variant: "destructive" }),
      },
    );
  };

  const remove = (id: string) => {
    deleteInstruction.mutate(
      { data: { id } },
      {
        onSuccess: () => {
          toast({ title: "Instruction deleted" });
          if (editingId === id) reset();
          onSaved();
        },
        onError: () => toast({ title: "Failed to delete instruction", variant: "destructive" }),
      },
    );
  };

  return (
    <section className="space-y-3">
      <h2 className={sectionTitleCls}>
        <ScrollText className="w-3.5 h-3.5" /> Standing Instructions ({instructions.length})
      </h2>

      <div className="space-y-1">
        {instructions.length === 0 ? (
          <div className="text-xs font-mono text-muted-foreground border border-border bg-card p-3">
            No standing instructions defined yet.
          </div>
        ) : (
          instructions.map((i) => (
            <div
              key={i.id}
              className="flex items-start justify-between gap-3 border border-border bg-card px-3 py-2 font-mono text-sm"
            >
              <div className="flex flex-col gap-1 min-w-0">
                <span className={`break-words ${i.active === false ? "text-muted-foreground line-through" : "text-foreground"}`}>
                  {i.text}
                </span>
                <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
                  {i.scope ?? "global"} · p{i.priority ?? 50}
                  {i.applies_to_channel ? ` · ch:${i.applies_to_channel}` : ""}
                  {i.applies_to_audience_role ? ` · role:${i.applies_to_audience_role}` : ""}
                  {i.active === false ? " · inactive" : ""}
                </span>
              </div>
              <div className="flex gap-1 shrink-0">
                <button
                  onClick={() => startEdit(i)}
                  className="text-muted-foreground hover:text-primary p-1"
                  aria-label="Edit instruction"
                >
                  <Pencil className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => remove(i.id)}
                  className="text-muted-foreground hover:text-destructive p-1"
                  aria-label="Delete instruction"
                  disabled={deleteInstruction.isPending}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="border border-border bg-card p-3 space-y-3">
        <div className="flex items-center justify-between">
          <span className={labelCls}>
            {editingId ? "Edit Instruction" : "Add Instruction"}
          </span>
          {editingId && (
            <button
              onClick={reset}
              className="text-[10px] font-mono text-muted-foreground hover:text-foreground flex items-center gap-1"
            >
              <X className="w-3 h-3" /> CANCEL
            </button>
          )}
        </div>
        <Textarea
          value={form.text}
          onChange={(e) => setForm({ ...form, text: e.target.value })}
          placeholder="Instruction text, e.g. 'Always reply in the user's language.'"
          className="font-mono text-sm rounded-none border-border bg-background min-h-[60px]"
        />
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1 flex flex-col">
            <label className={labelCls}>Scope</label>
            <Input
              value={form.scope}
              onChange={(e) => setForm({ ...form, scope: e.target.value })}
              placeholder="global"
              className="font-mono text-xs rounded-none border-border bg-background h-9"
            />
          </div>
          <div className="space-y-1 flex flex-col">
            <label className={labelCls}>Priority (0–100)</label>
            <Input
              type="number"
              min={0}
              max={100}
              value={form.priority}
              onChange={(e) => setForm({ ...form, priority: Number(e.target.value) })}
              className="font-mono text-xs rounded-none border-border bg-background h-9"
            />
          </div>
          <div className="space-y-1 flex flex-col">
            <label className={labelCls}>Channel filter</label>
            <Input
              value={form.applies_to_channel}
              onChange={(e) => setForm({ ...form, applies_to_channel: e.target.value })}
              placeholder="all channels (optional)"
              className="font-mono text-xs rounded-none border-border bg-background h-9"
            />
          </div>
          <div className="space-y-1 flex flex-col">
            <label className={labelCls}>Audience role filter</label>
            <Input
              value={form.applies_to_audience_role}
              onChange={(e) =>
                setForm({ ...form, applies_to_audience_role: e.target.value })
              }
              placeholder="all roles (optional)"
              className="font-mono text-xs rounded-none border-border bg-background h-9"
            />
          </div>
        </div>
        <label className="flex items-center gap-2 font-mono text-xs text-muted-foreground cursor-pointer">
          <input
            type="checkbox"
            checked={form.active}
            onChange={(e) => setForm({ ...form, active: e.target.checked })}
            className="accent-primary"
          />
          ACTIVE
        </label>
        <Button
          className="rounded-none h-9 text-[10px] font-mono bg-primary text-primary-foreground font-bold hover:bg-primary/90"
          disabled={saveInstruction.isPending || !form.text.trim()}
          onClick={save}
        >
          <Plus className="w-3.5 h-3.5 mr-2" />
          {editingId ? "UPDATE INSTRUCTION" : "ADD INSTRUCTION"}
        </Button>
      </div>
    </section>
  );
}
