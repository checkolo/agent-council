import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import {
  CassetteModeSelect,
  cassetteModeToRecorded,
  type CassetteMode,
} from "@/components/CassetteModeSelect";
import { CouncilPreview } from "@/components/CouncilPreview";
import { InputDropzone } from "@/components/InputDropzone";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/ui/button";
import {
  createRun,
  fetchDemoSamples,
  fetchHealth,
  fetchJudgeModels,
  fetchRun,
  fetchTemplates,
  type Template,
} from "@/lib/api";
import { cn } from "@/lib/cn";

export function NewRun() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [judgeModels, setJudgeModels] = useState<string[]>([]);
  const [demoSamples, setDemoSamples] = useState<
    Record<string, { filename: string; content: string }>
  >({});
  const [hasApiKey, setHasApiKey] = useState(true);
  const [template, setTemplate] = useState("pr-review");
  const [input, setInput] = useState("");
  const [filename, setFilename] = useState<string | null>(null);
  const [mode, setMode] = useState<"fast" | "thorough">("fast");
  const [maxCost, setMaxCost] = useState("0.50");
  const [cassetteMode, setCassetteMode] = useState<CassetteMode>("live");
  const [modelOverrides, setModelOverrides] = useState<Record<string, string>>({});
  const [activeRoles, setActiveRoles] = useState<string[]>([]);
  const [desiredOutcome, setDesiredOutcome] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [replayFrom, setReplayFrom] = useState<string | null>(null);

  useEffect(() => {
    fetchTemplates()
      .then(setTemplates)
      .catch(() => toast.error("Failed to load templates"));
    fetchJudgeModels()
      .then(setJudgeModels)
      .catch(() => {});
    fetchDemoSamples()
      .then(setDemoSamples)
      .catch(() => {});
    fetchHealth()
      .then((h) => {
        setHasApiKey(h.has_api_key);
        if (!h.has_api_key) setCassetteMode("replay");
      })
      .catch(() => {});
  }, []);

  const replayId = searchParams.get("replay");
  useEffect(() => {
    if (!replayId) return;
    fetchRun(replayId)
      .then((run) => {
        setTemplate(run.template);
        setInput(run.input_text);
        setMode(run.mode === "thorough" ? "thorough" : "fast");
        setCassetteMode("replay");
        setReplayFrom(replayId);
        setFilename(`${replayId}.txt`);
        toast.message(`Loaded run ${replayId} for free replay`);
      })
      .catch(() => toast.error(`Could not load run ${replayId}`));
  }, [replayId]);

  const selected = templates.find((t) => t.name === template);

  useEffect(() => {
    if (selected) {
      setMaxCost(selected.max_cost_usd.toFixed(2));
      setActiveRoles(selected.roles);
      setDesiredOutcome(selected.default_outcome);
    }
  }, [selected?.name, selected?.max_cost_usd, selected?.roles, selected?.default_outcome]);

  const handleTemplateChange = (name: string) => {
    setTemplate(name);
    setModelOverrides({});
    const t = templates.find((x) => x.name === name);
    setActiveRoles(t?.roles ?? []);
    setDesiredOutcome(t?.default_outcome ?? "");
  };

  const handleToggleRole = (key: string) => {
    setActiveRoles((prev) => {
      if (prev.includes(key)) {
        if (prev.length <= 1) {
          toast.error("Council needs at least one member");
          return prev;
        }
        return prev.filter((r) => r !== key);
      }
      const templateOrder = selected?.roles ?? [];
      const next = [...prev, key].sort(
        (a, b) => templateOrder.indexOf(a) - templateOrder.indexOf(b),
      );
      return next;
    });
  };

  const handleResetRoles = () => {
    if (selected) setActiveRoles(selected.roles);
    toast.message("Council reset to template defaults");
  };

  const handleOverrideChange = (key: string, model: string) => {
    setModelOverrides((prev) => ({ ...prev, [key]: model }));
  };

  const handleLoadSample = () => {
    const sample = demoSamples[template];
    if (!sample?.content) {
      toast.error("No sample input for this template");
      return;
    }
    setInput(sample.content);
    setFilename(sample.filename);
    toast.success(`Loaded ${sample.filename}`);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) {
      toast.error("Paste a diff, brief, or question");
      return;
    }
    if (cassetteMode === "live" && !hasApiKey) {
      toast.error("No API key — switch to Replay mode or add OPENROUTER_API_KEY");
      return;
    }
    setSubmitting(true);
    try {
      const overrides =
        Object.keys(modelOverrides).length > 0 ? modelOverrides : undefined;
      const roles =
        selected && activeRoles.length !== selected.roles.length
          ? activeRoles
          : selected &&
              activeRoles.some((r, i) => r !== selected.roles[i])
            ? activeRoles
            : undefined;
      const { run_id } = await createRun({
        template,
        input: input.trim(),
        mode,
        max_cost: parseFloat(maxCost) || undefined,
        recorded: cassetteModeToRecorded(cassetteMode),
        model_overrides: overrides,
        roles,
        desired_outcome: desiredOutcome || undefined,
      });
      toast.success(
        cassetteMode === "replay"
          ? `Replay started: ${run_id}`
          : `Run started: ${run_id}`,
      );
      navigate(`/runs/${run_id}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to start run");
    } finally {
      setSubmitting(false);
    }
  };

  const memberCount = activeRoles.length || selected?.roles.length || 4;
  const activeRoleDetails =
    selected?.role_details.filter((r) => activeRoles.includes(r.key)) ?? [];
  const selectedOutcome = selected?.outcomes.find((o) => o.id === desiredOutcome);
  const sampleLabel =
    template === "song-writer" ? "Load sample brief" : "Load sample diff";

  return (
    <div>
      <PageHeader
        eyebrow="02 · Composer"
        title={
          <>
            Compose a council <em className="font-serif italic font-normal">review</em>.
          </>
        }
        description="Pick a template, paste your input, and run live or replay from saved cassettes."
      />

      {replayFrom && (
        <div className="border border-border bg-muted/30 px-4 py-3 mb-8 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
          Replaying run {replayFrom} · no API cost · same template, input, and models required
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Template + council roster */}
        <section className="border-b border-border pb-8 mb-8">
          <label className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground block mb-3">
            Template
          </label>
          <div className="flex flex-wrap gap-2 mb-4">
            {templates.map((t) => (
              <button
                key={t.name}
                type="button"
                onClick={() => handleTemplateChange(t.name)}
                className={cn(
                  "font-mono text-[10px] uppercase tracking-wider border px-3 py-2 transition-colors",
                  template === t.name
                    ? "border-foreground bg-foreground text-background"
                    : "border-border hover:bg-muted/40",
                )}
              >
                {t.name}
              </button>
            ))}
          </div>
          {selected && (
            <>
              <p className="text-sm text-muted-foreground mb-4">{selected.description}</p>
              <div className="flex flex-wrap gap-2 mb-6">
                {activeRoleDetails.map((role) => (
                  <span
                    key={role.key}
                    className="font-mono text-[10px] uppercase tracking-wider border border-border px-2 py-1"
                  >
                    {role.display_name}
                  </span>
                ))}
              </div>
              <CouncilPreview
                roleDetails={selected.role_details}
                defaultRoleKeys={selected.roles}
                activeRoles={activeRoles}
                judgeModel={selected.judge_model}
                judgeModels={judgeModels}
                modelOverrides={modelOverrides}
                onOverrideChange={handleOverrideChange}
                onToggleRole={handleToggleRole}
                onResetRoles={handleResetRoles}
              />
            </>
          )}
        </section>

        {/* Desired outcome */}
        {selected && selected.outcomes.length > 0 && (
          <section className="border-b border-border pb-8 mb-8">
            <label className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground block mb-1">
              Desired outcome
            </label>
            <p className="text-sm text-muted-foreground mb-4">
              What the judge must deliver — regardless of panel disagreements.
            </p>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {selected.outcomes.map((outcome) => (
                <button
                  key={outcome.id}
                  type="button"
                  onClick={() => setDesiredOutcome(outcome.id)}
                  className={cn(
                    "text-left border p-4 transition-colors",
                    desiredOutcome === outcome.id
                      ? "border-foreground bg-foreground text-background"
                      : "border-border hover:bg-muted/40",
                  )}
                >
                  <p className="font-mono text-[10px] uppercase tracking-wider mb-1">
                    {outcome.label}
                  </p>
                  <p
                    className={cn(
                      "text-xs leading-relaxed",
                      desiredOutcome === outcome.id
                        ? "text-background/80"
                        : "text-muted-foreground",
                    )}
                  >
                    {outcome.description}
                  </p>
                </button>
              ))}
            </div>
          </section>
        )}

        {/* Input */}
        <section className="border-b border-border pb-8 mb-8">
          <label className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground block mb-3">
            Input
          </label>
          <InputDropzone
            value={input}
            onChange={setInput}
            filename={filename}
            onFilenameChange={setFilename}
          />
          <div className="flex flex-wrap gap-3 mt-4">
            <Button type="button" variant="outline" size="sm" onClick={handleLoadSample}>
              {sampleLabel}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => navigate("/cassette?sample=demo-auth")}
            >
              Try demo cassette
            </Button>
          </div>
        </section>

        {/* Options */}
        <section className="pb-8 mb-8">
          <label className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground block mb-3">
            Options
          </label>
          <div className="flex flex-wrap gap-8 mb-8">
            <div>
              <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-2">
                Mode
              </p>
              <div className="flex gap-2">
                {(["fast", "thorough"] as const).map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setMode(m)}
                    className={cn(
                      "font-mono text-[10px] uppercase tracking-wider border px-3 py-2 transition-colors",
                      mode === m
                        ? "border-foreground bg-foreground text-background"
                        : "border-border hover:bg-muted/40",
                    )}
                  >
                    {m}
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                ~$0.05–0.15 fast · ~$0.30+ thorough (estimate)
              </p>
            </div>

            <div>
              <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-2">
                Max cost (USD)
              </p>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={maxCost}
                onChange={(e) => setMaxCost(e.target.value)}
                disabled={cassetteMode === "replay"}
                className="font-mono text-sm border border-border bg-background px-3 py-2 w-32 focus:outline-none focus:ring-1 focus:ring-foreground disabled:opacity-50"
              />
            </div>
          </div>

          <CassetteModeSelect
            mode={cassetteMode}
            onChange={setCassetteMode}
            hasApiKey={hasApiKey}
          />
        </section>

        {/* Summary strip */}
        <div className="border border-border px-4 py-3 mb-6 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
          {template} · {memberCount} members · {mode} ·{" "}
          {cassetteMode === "replay" ? "replay" : `max $${maxCost}`}
          {selectedOutcome ? ` · ${selectedOutcome.label}` : ""}
        </div>

        <Button type="submit" disabled={submitting}>
          {submitting
            ? "Starting..."
            : cassetteMode === "replay"
              ? "Replay from cassettes"
              : "Start council review"}
        </Button>
      </form>
    </div>
  );
}
