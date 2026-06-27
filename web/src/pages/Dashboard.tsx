import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/ui/badge";
import { exportRunUrl, fetchRuns, type Run } from "@/lib/api";
import { useRunCount } from "@/context/RunCountContext";
import { cn } from "@/lib/cn";

const PAGE_SIZE = 20;

export function Dashboard() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [templateFilter, setTemplateFilter] = useState<string | undefined>();
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const { setRunCount } = useRunCount();

  const loadRuns = useCallback(
    async (nextOffset = 0, append = false) => {
      const data = await fetchRuns({
        limit: PAGE_SIZE,
        offset: nextOffset,
        template: templateFilter,
        status: statusFilter,
      });
      setRuns((prev) => (append ? [...prev, ...data.runs] : data.runs));
      setHasMore(data.runs.length === PAGE_SIZE);
      setOffset(nextOffset);
      if (!append) setRunCount(data.runs.length);
    },
    [templateFilter, statusFilter, setRunCount],
  );

  useEffect(() => {
    setLoading(true);
    loadRuns(0, false)
      .catch(() => setRuns([]))
      .finally(() => setLoading(false));
  }, [loadRuns]);

  useEffect(() => {
    const hasActive = runs.some(
      (r) => r.status !== "complete" && r.status !== "failed",
    );
    if (!hasActive && runs.length > 0) return;

    const interval = setInterval(() => {
      loadRuns(0, false).catch(() => {});
    }, 2000);

    return () => clearInterval(interval);
  }, [runs, loadRuns]);

  const templates = [...new Set(runs.map((r) => r.template))];
  const statuses = [...new Set(runs.map((r) => r.status))];

  return (
    <div>
      <PageHeader
        eyebrow="01 · Run History"
        title={
          <>
            Where the council <em className="font-serif italic font-normal">disagrees</em>.
          </>
        }
        description="Browse past reviews, replay Decision Reports, and share cassettes."
      />

      <div className="flex flex-wrap gap-4 mb-4 border-b border-border pb-4">
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground self-center">
          Template
        </span>
        <FilterChip
          label="All"
          active={!templateFilter}
          onClick={() => setTemplateFilter(undefined)}
        />
        {templates.map((t) => (
          <FilterChip
            key={t}
            label={t}
            active={templateFilter === t}
            onClick={() => setTemplateFilter(templateFilter === t ? undefined : t)}
          />
        ))}
      </div>

      <div className="flex flex-wrap gap-4 mb-8 border-b border-border pb-4">
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground self-center">
          Status
        </span>
        <FilterChip
          label="All"
          active={!statusFilter}
          onClick={() => setStatusFilter(undefined)}
        />
        {statuses.map((s) => (
          <FilterChip
            key={s}
            label={s}
            active={statusFilter === s}
            onClick={() => setStatusFilter(statusFilter === s ? undefined : s)}
          />
        ))}
      </div>

      {loading ? (
        <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
          Loading...
        </p>
      ) : runs.length === 0 ? (
        <div className="border border-border p-8 text-center">
          <p className="text-muted-foreground mb-4">No runs yet.</p>
          <Link
            to="/new"
            className="font-mono text-[11px] uppercase tracking-wider underline underline-offset-4"
          >
            Start a review →
          </Link>
        </div>
      ) : (
        <>
          <div className="grid gap-4">
            {runs.map((run) => (
              <div
                key={run.id}
                className="border border-border bg-background hover:bg-muted/40 transition-colors"
              >
                <Link to={`/runs/${run.id}`} className="block p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="muted">{run.template}</Badge>
                        <Badge variant={run.status === "complete" ? "success" : "default"}>
                          {run.status}
                        </Badge>
                        <Badge variant="muted">{run.mode}</Badge>
                      </div>
                      <p className="font-mono text-sm">{run.id}</p>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-1">
                        {run.input_text.slice(0, 120)}
                      </p>
                    </div>
                    <div className="text-right font-mono text-[11px] uppercase tracking-wider text-muted-foreground shrink-0">
                      <p className="tabular">${run.cost_usd?.toFixed(4) ?? "0.0000"}</p>
                      <p className="tabular">
                        {run.duration_ms ? `${(run.duration_ms / 1000).toFixed(0)}s` : "—"}
                      </p>
                      <p>{run.created_at?.slice(0, 10)}</p>
                    </div>
                  </div>
                </Link>
                {run.status === "complete" && (
                  <div className="border-t border-border px-4 py-2">
                    <a
                      href={exportRunUrl(run.id)}
                      download
                      className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground underline underline-offset-4"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Export
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>

          {hasMore && (
            <div className="mt-6 text-center">
              <button
                type="button"
                onClick={() => loadRuns(offset + PAGE_SIZE, true).catch(() => {})}
                className="font-mono text-[11px] uppercase tracking-wider border border-border px-4 py-2 hover:bg-muted/40"
              >
                Load more
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "font-mono text-[10px] uppercase tracking-wider border px-3 py-1 transition-colors",
        active
          ? "border-foreground bg-foreground text-background"
          : "border-border text-muted-foreground hover:bg-muted/40",
      )}
    >
      {label}
    </button>
  );
}
