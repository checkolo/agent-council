import { cn } from "@/lib/cn";

interface StatusStripProps {
  runCount?: number;
  hasApiKey?: boolean | null;
}

export function StatusStrip({ runCount = 0, hasApiKey = null }: StatusStripProps) {
  const date = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <div className="border-b border-border bg-muted/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-8 items-center gap-3 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
          <span>Quorum v0.1</span>
          <span className="h-3 w-px bg-border" />
          <span>{date}</span>
          <span className="h-3 w-px bg-border" />
          <span className="tabular">{runCount} runs</span>
          <span className="h-3 w-px bg-border" />
          {hasApiKey === null ? (
            <span>API key · …</span>
          ) : (
            <span
              className={cn(hasApiKey ? "text-success" : "text-warning")}
            >
              API key · {hasApiKey ? "set" : "recorded only"}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
