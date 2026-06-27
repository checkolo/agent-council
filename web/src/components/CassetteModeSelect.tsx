import { cn } from "@/lib/cn";

export type CassetteMode = "live" | "replay";

interface CassetteModeSelectProps {
  mode: CassetteMode;
  onChange: (mode: CassetteMode) => void;
  hasApiKey: boolean;
}

const MODES: {
  id: CassetteMode;
  label: string;
  description: string;
  detail: string;
}[] = [
  {
    id: "live",
    label: "Live",
    description: "Call OpenRouter — responses saved to cassettes/recordings/",
    detail: "Same as CLI --record. Re-run later with Replay for free.",
  },
  {
    id: "replay",
    label: "Replay",
    description: "No API calls — reuse saved recordings",
    detail: "Same as CLI --recorded. Needs matching prior live run.",
  },
];

export function CassetteModeSelect({
  mode,
  onChange,
  hasApiKey,
}: CassetteModeSelectProps) {
  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-2">
        Cassette mode
      </p>
      <div className="grid gap-2 sm:grid-cols-2 max-w-2xl">
        {MODES.map((m) => {
          const disabled = m.id === "live" && !hasApiKey;
          return (
            <button
              key={m.id}
              type="button"
              disabled={disabled}
              onClick={() => onChange(m.id)}
              className={cn(
                "text-left border p-4 transition-colors",
                mode === m.id
                  ? "border-foreground bg-foreground text-background"
                  : "border-border hover:bg-muted/40",
                disabled && "opacity-50 cursor-not-allowed hover:bg-transparent",
              )}
            >
              <p className="font-mono text-[10px] uppercase tracking-wider mb-1">
                {m.label}
                {disabled ? " · no API key" : ""}
              </p>
              <p
                className={cn(
                  "text-xs leading-relaxed",
                  mode === m.id ? "text-background/80" : "text-muted-foreground",
                )}
              >
                {m.description}
              </p>
            </button>
          );
        })}
      </div>
      <p className="text-xs text-muted-foreground mt-3 max-w-2xl">
        {MODES.find((m) => m.id === mode)?.detail}
        {" · "}
        Export full runs as <span className="font-mono">.cassette</span> from a completed run page.
      </p>
    </div>
  );
}

export function cassetteModeToRecorded(mode: CassetteMode): boolean {
  return mode === "replay";
}
