import { cn } from "@/lib/cn";

type Phase = "panel" | "review" | "judge" | "done";

interface RunStatusRailProps {
  phase: Phase;
  mode: string;
}

const STEPS: { key: Phase; label: string; thoroughOnly?: boolean }[] = [
  { key: "panel", label: "Panel" },
  { key: "review", label: "Peer Review", thoroughOnly: true },
  { key: "judge", label: "Judge" },
  { key: "done", label: "Complete" },
];

export function RunStatusRail({ phase, mode }: RunStatusRailProps) {
  const steps = STEPS.filter((s) => !s.thoroughOnly || mode === "thorough");
  const phaseOrder = steps.map((s) => s.key);
  const currentIdx = phaseOrder.indexOf(phase);

  return (
    <div className="flex items-center border border-border mb-8">
      {steps.map((step, i) => {
        const isActive = i === currentIdx;
        const isDone = i < currentIdx;
        return (
          <div
            key={step.key}
            className={cn(
              "flex-1 px-4 py-3 font-mono text-[11px] uppercase tracking-wider text-center border-r border-border last:border-r-0 transition-colors",
              isActive && "bg-foreground text-background",
              isDone && !isActive && "text-success",
              !isActive && !isDone && "text-muted-foreground",
            )}
          >
            {step.label}
          </div>
        );
      })}
    </div>
  );
}
