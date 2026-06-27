import { Scale } from "lucide-react";
import type { DecisionReport } from "@/lib/api";
import { cn } from "@/lib/cn";

interface JudgeVerdictProps {
  deliverable?: string;
  streamingContent?: string;
  isStreaming?: boolean;
  markdownFallback?: string;
  recommendation?: string;
  outcomeLabel?: string;
}

export function JudgeVerdict({
  deliverable,
  streamingContent,
  isStreaming,
  markdownFallback,
  recommendation,
  outcomeLabel,
}: JudgeVerdictProps) {
  const content =
    deliverable?.trim() ||
    (isStreaming ? streamingContent : "") ||
    markdownFallback?.trim() ||
    recommendation?.trim() ||
    "";

  if (!content && !isStreaming) {
    return null;
  }

  return (
    <section className="border-2 border-foreground mb-8">
      <div className="flex items-center gap-2 border-b border-border px-6 py-4 bg-muted/30">
        <Scale className="h-4 w-4" />
        <h2 className="font-mono text-[11px] uppercase tracking-wider">
          Judge&apos;s Verdict
        </h2>
        {outcomeLabel && (
          <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground ml-auto">
            {outcomeLabel}
          </span>
        )}
        {isStreaming && (
          <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground ml-auto animate-pulse">
            Synthesizing…
          </span>
        )}
      </div>
      <div className={cn("px-6 py-5", isStreaming && !deliverable && "opacity-90")}>
        {content ? (
          <div className="text-sm whitespace-pre-wrap leading-relaxed">{content}</div>
        ) : (
          <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
            Awaiting judge synthesis…
          </p>
        )}
      </div>
    </section>
  );
}

export function verdictFromReport(report: DecisionReport): {
  deliverable: string;
  markdownFallback?: string;
  recommendation?: string;
} {
  return {
    deliverable: report.deliverable ?? "",
    markdownFallback: (report as DecisionReport & { markdown_fallback?: string }).markdown_fallback,
    recommendation: report.recommendation?.action,
  };
}
