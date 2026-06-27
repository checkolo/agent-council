import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { DecisionReportCard } from "@/components/DecisionReportCard";
import { IdentityToggle } from "@/components/IdentityToggle";
import { JudgeVerdict, verdictFromReport } from "@/components/JudgeVerdict";
import { LiveMemberTabs } from "@/components/LiveMemberTabs";
import { PeerReviewTabs } from "@/components/PeerReviewTabs";
import { RunStatusRail } from "@/components/RunStatusRail";
import { useIdentity } from "@/context/IdentityContext";
import { useRunStream } from "@/hooks/useRunStream";
import { Badge } from "@/ui/badge";
import {
  deriveInputLabel,
  exportRunUrl,
  fetchRun,
  type DecisionReport,
  type Run,
} from "@/lib/api";

export function RunView() {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<Run | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { showIdentity, toggleIdentity } = useIdentity();

  const refetchRun = useCallback(async () => {
    if (!id) return;
    const r = await fetchRun(id);
    setRun(r);
  }, [id]);

  const stream = useRunStream(id, run?.status, refetchRun);

  useEffect(() => {
    if (!id) return;
    fetchRun(id)
      .then(setRun)
      .catch(() => setError("Run not found"));
  }, [id]);

  if (error) {
    return (
      <div className="border border-border p-8 text-center">
        <p className="text-destructive mb-4">{error}</p>
        <Link to="/" className="font-mono text-[11px] uppercase tracking-wider underline">
          ← Back to history
        </Link>
      </div>
    );
  }

  if (!run) {
    return (
      <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
        Loading run...
      </p>
    );
  }

  const report = run.decision_report as DecisionReport | undefined;
  const members = report?.member_outputs ?? [];
  const memberCount =
    members.length ||
    Object.keys(stream.members).length ||
    4;
  const inputLabel = deriveInputLabel(run.input_text);
  const phase = run.status === "complete" ? "done" : stream.phase;
  const isComplete = run.status === "complete";
  const isJudgePhase = phase === "judge" || phase === "done";
  const verdict = report ? verdictFromReport(report) : null;
  const showVerdict =
    isJudgePhase &&
    (verdict?.deliverable ||
      stream.judgeContent ||
      verdict?.markdownFallback ||
      verdict?.recommendation ||
      stream.judgeDone ||
      isComplete);

  return (
    <div>
      <Link
        to="/"
        className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground hover:text-foreground mb-6 inline-block"
      >
        ← History
      </Link>

      <div className="flex flex-wrap items-center gap-3 border-b border-border pb-4 mb-8 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
        <span>{run.template}</span>
        <span className="h-3 w-px bg-border" />
        <span>{inputLabel}</span>
        <span className="h-3 w-px bg-border" />
        <span>{memberCount} members</span>
        <span className="h-3 w-px bg-border" />
        <span className="tabular">${run.cost_usd?.toFixed(2) ?? "—"}</span>
        <span className="h-3 w-px bg-border" />
        <span className="tabular">
          {run.duration_ms ? `${(run.duration_ms / 1000).toFixed(0)}s` : "—"}
        </span>
        <span className="h-3 w-px bg-border" />
        <Badge variant={isComplete ? "success" : "default"}>
          {run.status}
        </Badge>
        {isComplete && (
          <>
            <span className="h-3 w-px bg-border" />
            <Link
              to={`/new?replay=${run.id}`}
              className="font-mono text-[10px] uppercase border border-border px-3 py-1.5 hover:bg-muted/40"
            >
              Replay free
            </Link>
            <span className="h-3 w-px bg-border" />
            <a
              href={exportRunUrl(run.id)}
              download
              className="font-mono text-[10px] uppercase border border-border px-3 py-1.5 hover:bg-muted/40"
            >
              Export .cassette
            </a>
          </>
        )}
      </div>

      <RunStatusRail phase={phase} mode={run.mode} />

      {run.status === "failed" && run.error && (
        <div className="border border-destructive bg-destructive/5 px-6 py-4 mb-8">
          <p className="font-mono text-[11px] uppercase tracking-wider text-destructive mb-2">
            Run failed
          </p>
          <p className="text-sm">{run.error}</p>
        </div>
      )}

      {showVerdict && (
        <JudgeVerdict
          deliverable={verdict?.deliverable}
          streamingContent={stream.judgeContent}
          isStreaming={phase === "judge" && !isComplete}
          markdownFallback={verdict?.markdownFallback}
          recommendation={verdict?.recommendation}
        />
      )}

      {!showVerdict && !isComplete && (
        <div className="border border-border p-6 mb-8 text-center">
          <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
            Council is deliberating...
          </p>
        </div>
      )}

      {report && (
        <div className="mb-8">
          <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-3">
            Deliberation report
          </p>
          <DecisionReportCard report={report} hideDeliverable />
        </div>
      )}

      {run.status === "failed" && !report && stream.judgeContent && (
        <JudgeVerdict streamingContent={stream.judgeContent} />
      )}

      <div className="mt-10">
        <IdentityToggle hidden={!showIdentity} onToggle={toggleIdentity} />
        <LiveMemberTabs
          streamingMembers={stream.members}
          reportMembers={members.length > 0 ? members : undefined}
          showIdentity={showIdentity}
        />
        {(run.mode === "thorough" || (report?.peer_reviews?.length ?? 0) > 0) && (
          <PeerReviewTabs
            peerReviews={stream.peerReviews}
            reportReviews={report?.peer_reviews}
          />
        )}
      </div>
    </div>
  );
}
