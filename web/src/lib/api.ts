export interface RoleDetail {
  key: string;
  display_name: string;
  suggested_models: string[];
}

export interface OutcomeOption {
  id: string;
  label: string;
  description: string;
}

export interface Template {
  name: string;
  description: string;
  roles: string[];
  role_details: RoleDetail[];
  judge_model: string;
  mode: string;
  max_cost_usd: number;
  default_outcome: string;
  outcomes: OutcomeOption[];
}

export interface Run {
  id: string;
  template: string;
  input_text: string;
  mode: string;
  status: string;
  decision_report?: DecisionReport;
  cost_usd: number;
  duration_ms: number;
  max_cost?: number;
  error?: string;
  created_at: string;
  completed_at?: string;
}

export interface Disagreement {
  topic: string;
  positions: Record<string, string>;
  resolution: string;
  chosen_position: string;
}

export interface Risk {
  description: string;
  severity: "blocker" | "major" | "minor" | "nit";
}

export interface Recommendation {
  action: string;
  evidence: string[];
}

export interface Attribution {
  role: string;
  idea: string;
}

export interface MemberOutput {
  role: string;
  model: string;
  content: string;
  alias?: string;
}

export interface DecisionReport {
  task_id: string;
  template: string;
  deliverable: string;
  consensus: string[];
  disagreements: Disagreement[];
  risks: Risk[];
  unknowns: string[];
  recommendation: Recommendation;
  attribution: Attribution[];
  member_outputs: MemberOutput[];
  peer_reviews: { reviewer_role: string; content: string }[];
  cost_usd: number;
  duration_ms: number;
  cassette_path?: string;
  markdown_fallback?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  has_api_key: boolean;
}

const BASE = "";

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE}/api/health`);
  if (!res.ok) throw new Error("Failed to fetch health");
  return res.json();
}

export async function fetchTemplates(): Promise<Template[]> {
  const res = await fetch(`${BASE}/api/templates`);
  if (!res.ok) throw new Error("Failed to fetch templates");
  return res.json();
}

export async function fetchJudgeModels(): Promise<string[]> {
  const res = await fetch(`${BASE}/api/models`);
  if (!res.ok) throw new Error("Failed to fetch models");
  const data = await res.json();
  return data.judge_models ?? [];
}

export async function fetchSampleDiff(): Promise<string> {
  const res = await fetch(`${BASE}/api/demo/sample-diff`);
  if (!res.ok) throw new Error("Failed to fetch sample diff");
  const data = await res.json();
  return data.content;
}

export async function fetchSampleBrief(): Promise<string> {
  const res = await fetch(`${BASE}/api/demo/sample-brief`);
  if (!res.ok) throw new Error("Failed to fetch sample brief");
  const data = await res.json();
  return data.content;
}

export async function fetchDemoSamples(): Promise<
  Record<string, { filename: string; content: string }>
> {
  const res = await fetch(`${BASE}/api/demo/samples`);
  if (!res.ok) throw new Error("Failed to fetch demo samples");
  const data = await res.json();
  return data.samples ?? {};
}

export async function fetchRuns(params?: {
  limit?: number;
  offset?: number;
  template?: string;
  status?: string;
}): Promise<{ runs: Run[]; limit: number; offset: number }> {
  const q = new URLSearchParams();
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  if (params?.template) q.set("template", params.template);
  if (params?.status) q.set("status", params.status);
  const res = await fetch(`${BASE}/api/runs?${q}`);
  if (!res.ok) throw new Error("Failed to fetch runs");
  return res.json();
}

export async function fetchRun(id: string): Promise<Run> {
  const res = await fetch(`${BASE}/api/runs/${id}`);
  if (!res.ok) throw new Error("Run not found");
  return res.json();
}

export async function createRun(body: {
  template: string;
  input: string;
  mode: string;
  max_cost?: number;
  recorded?: boolean;
  model_overrides?: Record<string, string>;
  roles?: string[];
  desired_outcome?: string;
}): Promise<{ run_id: string }> {
  const res = await fetch(`${BASE}/api/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let message = "Failed to create run";
    try {
      const err = await res.json();
      if (typeof err.detail === "string") message = err.detail;
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  return res.json();
}

export async function uploadCassette(file: File): Promise<Record<string, unknown>> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/api/cassettes/view`, { method: "POST", body: form });
  if (!res.ok) throw new Error("Invalid cassette");
  return res.json();
}

export async function fetchSampleCassette(name: string): Promise<Record<string, unknown>> {
  const res = await fetch(`${BASE}/api/cassettes/samples/${name}`);
  if (!res.ok) throw new Error("Sample not found");
  return res.json();
}

export function exportRunUrl(runId: string): string {
  return `${BASE}/api/runs/${runId}/export`;
}

export function deriveInputLabel(input: string): string {
  const firstLine = input.split("\n")[0]?.trim() ?? "";
  if (firstLine.startsWith("diff --git")) {
    const match = firstLine.match(/b\/(.+)$/);
    if (match) return match[1];
  }
  if (input.length > 30) return `${input.slice(0, 30)}…`;
  return input || "input";
}
