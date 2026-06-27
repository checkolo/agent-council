import { Check, X, AlertTriangle, ArrowRight } from "lucide-react";
import type { DecisionReport } from "@/lib/api";
import { Badge, severityVariant } from "@/ui/badge";

interface DecisionReportCardProps {
  report: DecisionReport;
  hideDeliverable?: boolean;
}

export function DecisionReportCard({ report, hideDeliverable }: DecisionReportCardProps) {
  return (
    <div className="border border-border">
      {!hideDeliverable && report.deliverable?.trim() && (
        <Section title="Deliverable">
          <div className="text-sm whitespace-pre-wrap leading-relaxed">
            {report.deliverable}
          </div>
        </Section>
      )}

      <Section title="Consensus" icon={<Check className="h-4 w-4 text-success" />}>
        {report.consensus.length === 0 ? (
          <p className="text-sm text-muted-foreground">No consensus identified.</p>
        ) : (
          <ul className="space-y-2">
            {report.consensus.map((item, i) => (
              <li key={i} className="text-sm flex gap-2">
                <Check className="h-4 w-4 text-success shrink-0 mt-0.5" />
                {item}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Disagreements" icon={<X className="h-4 w-4 text-destructive" />}>
        {report.disagreements.length === 0 ? (
          <p className="text-sm text-muted-foreground">No disagreements.</p>
        ) : (
          <ul className="space-y-4">
            {report.disagreements.map((d, i) => (
              <li key={i} className="text-sm">
                <p className="font-medium">{d.topic}</p>
                {Object.entries(d.positions).map(([role, pos]) => (
                  <p key={role} className="text-muted-foreground ml-4 mt-1">
                    {role}: {pos}
                  </p>
                ))}
                {d.resolution && (
                  <p className="mt-2 text-muted-foreground border-l-2 border-border pl-3">
                    → {d.resolution}
                  </p>
                )}
                {d.chosen_position && (
                  <p className="mt-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                    → Adopted: {d.chosen_position}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Risks" icon={<AlertTriangle className="h-4 w-4 text-warning" />}>
        {report.risks.length === 0 ? (
          <p className="text-sm text-muted-foreground">No risks identified.</p>
        ) : (
          <ul className="space-y-2">
            {report.risks.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <Badge variant={severityVariant(r.severity)}>{r.severity}</Badge>
                {r.description}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Unknowns" icon={<AlertTriangle className="h-4 w-4 text-muted-foreground" />}>
        {report.unknowns.length === 0 ? (
          <p className="text-sm text-muted-foreground">None identified</p>
        ) : (
          <ul className="space-y-2">
            {report.unknowns.map((item, i) => (
              <li key={i} className="text-sm list-disc ml-4">
                {item}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Recommendation" icon={<ArrowRight className="h-4 w-4" />}>
        <p className="text-sm font-medium">{report.recommendation.action}</p>
        {report.recommendation.evidence.map((ev, i) => (
          <p key={i} className="text-sm text-muted-foreground font-mono mt-1">
            → {ev}
          </p>
        ))}
      </Section>

      <Section title="Attribution">
        {report.attribution.length === 0 ? (
          <p className="text-sm text-muted-foreground">No attribution recorded.</p>
        ) : (
          <ul className="space-y-1">
            {report.attribution.map((a, i) => (
              <li key={i} className="text-sm font-mono">
                [{a.role}] → {a.idea}
              </li>
            ))}
          </ul>
        )}
      </Section>
    </div>
  );
}

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="border-b border-border p-6 last:border-b-0">
      <div className="flex items-center gap-2 mb-4">
        {icon}
        <h3 className="font-mono text-[11px] uppercase tracking-wider">{title}</h3>
      </div>
      {children}
    </div>
  );
}
