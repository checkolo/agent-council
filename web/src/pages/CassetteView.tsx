import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { CassetteDropzone } from "@/components/CassetteDropzone";
import { DecisionReportCard } from "@/components/DecisionReportCard";
import { JudgeVerdict, verdictFromReport } from "@/components/JudgeVerdict";
import { MemberTabs } from "@/components/MemberTabs";
import { IdentityToggle } from "@/components/IdentityToggle";
import { RunStatusRail } from "@/components/RunStatusRail";
import { useIdentity } from "@/context/IdentityContext";
import { fetchSampleCassette, type DecisionReport } from "@/lib/api";
import { Button } from "@/ui/button";

export function CassetteView() {
  const [searchParams] = useSearchParams();
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const { showIdentity, toggleIdentity } = useIdentity();
  const [loadingSample, setLoadingSample] = useState(false);

  const sample = searchParams.get("sample");

  useEffect(() => {
    if (!sample) return;
    setLoadingSample(true);
    fetchSampleCassette(sample)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoadingSample(false));
  }, [sample]);

  const report = data?.decision_report as DecisionReport | undefined;

  return (
    <div>
      <PageHeader
        eyebrow="03 · Cassette Viewer"
        title={
          <>
            Replay a shared <em className="font-serif italic font-normal">cassette</em>.
          </>
        }
        description="Inspect offline Decision Reports from .cassette files — no API key required."
      />

      <div className="flex flex-wrap gap-3 mb-6">
        <Button
          variant="outline"
          size="sm"
          disabled={loadingSample}
          onClick={() => {
            setLoadingSample(true);
            fetchSampleCassette("demo-auth")
              .then(setData)
              .finally(() => setLoadingSample(false));
          }}
        >
          demo-auth
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={loadingSample}
          onClick={() => {
            setLoadingSample(true);
            fetchSampleCassette("demo-arch")
              .then(setData)
              .finally(() => setLoadingSample(false));
          }}
        >
          demo-arch
        </Button>
      </div>

      <CassetteDropzone onLoad={setData} />

      {report && (
        <div className="mt-10">
          <div className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-6">
            Run: {String(data?.run_id ?? "")} · Template: {String(data?.template ?? "")}
          </div>
          <RunStatusRail phase="done" mode={String(data?.mode ?? "fast")} />
          <JudgeVerdict {...verdictFromReport(report)} />
          <div className="mt-8">
            <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground mb-3">
              Deliberation report
            </p>
            <DecisionReportCard report={report} hideDeliverable />
          </div>
          {report.member_outputs?.length > 0 && (
            <div className="mt-10">
              <IdentityToggle hidden={!showIdentity} onToggle={toggleIdentity} />
              <MemberTabs members={report.member_outputs} showIdentity={showIdentity} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
