/**
 * Runtime contracts for every response the UI reads.
 *
 * Each Zod schema is a projection of a type generated from the backend's OpenAPI document
 * (`generated.ts`, written by `ffia schemas export`). `contractChecks` fails to compile when the
 * backend renames, removes or retypes a field the UI depends on.
 */
import { z } from "zod";
import type * as G from "./generated";

type DeepRequired<T> = T extends readonly [unknown, ...unknown[]]
  ? { -readonly [K in keyof T]: DeepRequired<T[K]> }
  : T extends readonly (infer U)[]
    ? DeepRequired<U>[]
    : T extends object
      ? { -readonly [K in keyof T]-?: DeepRequired<Exclude<T[K], undefined>> }
      : T;

/** `true` when every server response of type `Full` satisfies the UI view `View`. */
type Conforms<Full, View> = [DeepRequired<Full>] extends [View] ? true : never;

const level = z.enum(["executive", "l100", "l200", "l300", "l400"]);
const capabilityStatus = z.enum([
  "GA",
  "PREVIEW",
  "MIXED",
  "DEPRECATED",
  "UNKNOWN/NEEDS VALIDATION",
  "LOCAL",
]);
const operatingMode = z.enum(["LIVE", "HYBRID", "OFFLINE"]);
const executionLabel = z.enum([
  "LIVE",
  "HYBRID",
  "LOCAL",
  "SIMULATED",
  "MOCKED",
  "PREVIEW",
  "UNAVAILABLE",
]);
const evidenceCategory = z.enum([
  "SIMULATED LOCALLY",
  "DOCUMENTED FABRIC BEHAVIOR",
  "DOCUMENTED BEHAVIOR",
  "REQUIRES TENANT VALIDATION",
  "ASSUMPTION",
  "PRODUCTION RECOMMENDATION",
  "PREVIEW LIMITATION",
  "VERIFIED LIVE",
]);
const changeStatus = z.enum([
  "PROPOSED",
  "BLOCKED",
  "APPROVED",
  "REJECTED",
  "EXECUTED",
  "VERIFIED",
  "FAILED",
]);
const itemType = z.enum(["Lakehouse", "Notebook", "SemanticModel", "Report"]);
const scalar = z.union([z.string(), z.number(), z.boolean(), z.null()]);

// ------------------------------------------------------------------ runtime and demo
export const providerStatusSchema = z.object({
  capability: z.string(),
  name: z.string(),
  kind: z.enum(["LIVE", "LOCAL", "FAULT-INJECTION", "NOT AVAILABLE"]),
  configured: z.boolean(),
  ready: z.boolean(),
  note: z.string(),
});

export const runtimeStatusSchema = z.object({
  operating_mode: operatingMode,
  environment: z.string(),
  overlay: z.string(),
  data_provider: z.string(),
  agent_provider: z.string(),
  mcp: z.string(),
  identity: z.string(),
  write_mode: z.string(),
  preview_features: z.array(z.string()),
  providers: z.array(providerStatusSchema),
  built_profiles: z.array(z.string()),
});
export type RuntimeStatus = z.output<typeof runtimeStatusSchema>;

export const demoCheckReportSchema = z.object({
  lines: z.array(z.object({ component: z.string(), status: z.string(), detail: z.string() })),
  recommended_mode: operatingMode,
  reason: z.string(),
});
export type DemoCheckReport = z.output<typeof demoCheckReportSchema>;

export const demoStepSchema = z.object({
  act: z.number(),
  title: z.string(),
  required: z.boolean(),
  passed: z.boolean(),
  label: z.string(),
  summary: z.string(),
  evidence: z.array(z.string()),
});
export const offlineDemoReportSchema = z.object({
  passed: z.boolean(),
  operating_mode: operatingMode,
  steps: z.array(demoStepSchema),
  label_counts: z.record(z.string(), z.number()),
  live_operations: z.number(),
  cloud_operations: z.number(),
});
export type OfflineDemoReport = z.output<typeof offlineDemoReportSchema>;

// ------------------------------------------------------------------ patterns
export const patternSchema = z.object({
  id: z.string(),
  name: z.string(),
  summary: z.string(),
  status: z.enum(["GA", "PREVIEW", "MIXED"]),
  preview_dependencies: z.array(z.string()),
  default_demo_path: z.enum(["LOCAL", "HYBRID", "DOCUMENTATION"]),
  when_to_use: z.string(),
  when_not_to_use: z.string(),
  fabric_role: z.string(),
  foundry_role: z.string(),
  mcp_role: z.string(),
  authority: z.string(),
  offline_equivalent: z.string(),
  selection_signals: z.array(z.string()),
  sources: z.array(z.string()),
});
export type Pattern = z.output<typeof patternSchema>;

export const recommendationSchema = z.object({
  pattern_id: z.string(),
  name: z.string(),
  score: z.number(),
  matched_needs: z.array(z.string()),
  status: z.enum(["GA", "PREVIEW", "MIXED"]),
  preview_dependencies: z.array(z.string()),
  default_demo_path: z.string(),
  why: z.string(),
});
export type Recommendation = z.output<typeof recommendationSchema>;

export const selectionSignalSchema = z.object({ id: z.string(), description: z.string() });
export type SelectionSignal = z.output<typeof selectionSignalSchema>;

// ------------------------------------------------------------------ guides
export const rehearsalSchema = z.object({
  operation: z.string(),
  item_type: itemType,
  item_name: z.string(),
  note: z.string(),
});
export type Rehearsal = z.output<typeof rehearsalSchema>;

export const guideStepSchema = z.object({
  id: z.string(),
  title: z.string(),
  objective: z.string(),
  copilot_prompt: z.string(),
  claude_code_prompt: z.string(),
  tool_path: z.object({
    provider: z.string(),
    server: z.string().nullable(),
    tools: z.array(z.string()),
    substitution_allowed: z.boolean(),
  }),
  writes: z.boolean(),
  approval_required: z.boolean(),
  checkpoint: z.string(),
  evidence_required: z.array(z.string()),
  not_evidence: z.array(z.string()),
  offline_equivalent: z.string(),
  offline_command: z.string().nullable(),
  failure_modes: z.array(z.string()),
  requires_windows: z.boolean(),
  rehearsal: rehearsalSchema.nullable(),
  diagram_focus: z.array(z.string()),
});
export type GuideStep = z.output<typeof guideStepSchema>;

export const guideSchema = z.object({
  id: z.string(),
  title: z.string(),
  industry: z.string(),
  scenario: z.string(),
  summary: z.string(),
  version: z.string(),
  status: z.enum(["draft", "validated-offline", "validated-live"]),
  patterns: z.array(z.string()),
  maturity_levels: z.array(z.string()),
  harnesses: z.array(z.string()),
  operating_rules: z.array(z.string()),
  tools: z.array(
    z.object({
      name: z.string(),
      purpose: z.string(),
      version: z.string().nullable(),
      status: z.string(),
      install: z.string(),
      required: z.boolean(),
    }),
  ),
  dataset_profile: z.string(),
  expected_baseline: z.string(),
  diagram: z.string().nullable(),
  steps: z.array(guideStepSchema),
});
export type Guide = z.output<typeof guideSchema>;

// ------------------------------------------------------------------ changes and audit
const fabricTargetSchema = z.object({
  workspace_alias: z.string(),
  item_type: itemType,
  item_name: z.string(),
  destination: z.enum(["LOCAL", "LIVE"]),
});
const checkResultSchema = z.object({
  name: z.string(),
  passed: z.boolean(),
  detail: z.string(),
  category: evidenceCategory,
});

export const proposedChangeSchema = z.object({
  change_id: z.string(),
  correlation_id: z.string(),
  operation: z.string(),
  target: fabricTargetSchema,
  provider: z.string(),
  reason: z.string(),
  requested_by: z.string(),
  risk: z.enum(["low", "medium", "high"]),
  reversible: z.boolean(),
  expected_impact: z.string(),
  validation: z.array(z.string()),
  rollback: z.string(),
  approval_required: z.boolean(),
  policy_allowed: z.boolean(),
  policy_reasons: z.array(z.string()),
  precondition: checkResultSchema,
  status: changeStatus,
});
export type ProposedChange = z.output<typeof proposedChangeSchema>;

export const approvalSchema = z.object({
  approval_id: z.string(),
  change_id: z.string(),
  approver: z.string(),
  decision: z.enum(["APPROVED", "REJECTED"]),
  expires_at: z.string(),
});
export type Approval = z.output<typeof approvalSchema>;

export const executionResultSchema = z.object({
  change_id: z.string(),
  approval_id: z.string(),
  status: changeStatus,
  execution_label: executionLabel,
  verification: checkResultSchema,
  rollback: z.string(),
});

export const auditRecordSchema = z.object({
  audit_id: z.string(),
  correlation_id: z.string(),
  timestamp: z.string(),
  actor: z.string(),
  action: z.string(),
  capability: z.string(),
  selected_provider: z.string(),
  execution_label: executionLabel,
  cloud_operation_performed: z.boolean(),
  success: z.boolean(),
});
export type AuditRecord = z.output<typeof auditRecordSchema>;

// ------------------------------------------------------------------ envelopes and payloads
const envelopeBase = z.object({
  operating_mode: operatingMode,
  execution_label: executionLabel,
  requested_provider: z.string(),
  selected_provider: z.string(),
  cloud_operation_performed: z.boolean(),
  equivalent_fabric_service: z.string(),
  teaching_objective: z.string(),
  correlation_id: z.string(),
  fallback_used: z.boolean(),
  fallback_reason: z.string().nullable(),
  simulation_notice: z.string().nullable(),
});
export type EnvelopeMeta = z.output<typeof envelopeBase>;

/** An execution envelope whose `data` is validated by `data`. */
export function envelopeSchema<T extends z.ZodType>(data: T) {
  return envelopeBase.extend({ data });
}

export const workspaceSchema = z.object({ id: z.string(), display_name: z.string() });
export const itemSchema = z.object({
  id: z.string(),
  display_name: z.string(),
  type: z.enum(["Lakehouse", "SemanticModel"]),
  workspace_id: z.string(),
});
const columnSchema = z.object({ name: z.string(), data_type: z.string() });
export const tableInfoSchema = z.object({
  name: z.string(),
  layer: z.string(),
  row_count: z.number().nullable(),
  columns: z.array(columnSchema),
});
export type TableInfo = z.output<typeof tableInfoSchema>;
export const tablePreviewSchema = z.object({
  table: z.string(),
  layer: z.string(),
  columns: z.array(columnSchema),
  rows: z.array(z.record(z.string(), scalar)),
  total_rows: z.number(),
  truncated: z.boolean(),
});
export type TablePreview = z.output<typeof tablePreviewSchema>;
export const evaluationResultSchema = z.object({
  profile: z.string(),
  observed_label: z.string(),
  tolerance: z.number(),
  compared: z.number(),
  passed: z.number(),
  pass_rate: z.number(),
  gate_passed: z.boolean(),
  comparisons: z.array(
    z.object({
      name: z.string(),
      expected: z.number().nullable(),
      observed: z.number().nullable(),
      absolute_difference: z.number().nullable(),
      passed: z.boolean(),
    }),
  ),
});
export type EvaluationResult = z.output<typeof evaluationResultSchema>;

// ------------------------------------------------------------------ education
export const lessonSummarySchema = z.object({
  id: z.string(),
  area: z.string(),
  title: z.string(),
  summary: z.string(),
  status: capabilityStatus,
  pattern_ids: z.array(z.string()),
  related_labs: z.array(z.string()),
  related_guides: z.array(z.string()),
});
export type LessonSummary = z.output<typeof lessonSummarySchema>;

export const lessonSchema = lessonSummarySchema.extend({
  learning_objectives: z.array(z.string()),
  prerequisites: z.array(z.string()),
  concepts: z.array(z.object({ term: z.string(), definition: z.string() })),
  evidence: z.array(
    z.object({ statement: z.string(), category: evidenceCategory, sources: z.array(z.string()) }),
  ),
  try_it: z.array(
    z.object({
      label: z.string(),
      command: z.string(),
      result_label: z.enum(["LOCAL", "SIMULATED", "HYBRID", "PREVIEW", "UNAVAILABLE"]),
    }),
  ),
  copilot_prompt: z.string(),
  claude_code_prompt: z.string(),
  production_notes: z.array(z.string()),
  sources: z.array(z.string()),
  levels: z.array(z.object({ level, label: z.string(), markdown: z.string() })),
  checks: z.array(
    z.object({ id: z.string(), level, question: z.string(), choices: z.array(z.string()) }),
  ),
});
export type Lesson = z.output<typeof lessonSchema>;
export type KnowledgeCheck = Lesson["checks"][number];

export const checkGradeSchema = z.object({
  check_id: z.string(),
  correct: z.boolean(),
  correct_choice: z.number(),
  explanation: z.string(),
});
export type CheckGrade = z.output<typeof checkGradeSchema>;

export const labSummarySchema = z.object({
  id: z.string(),
  title: z.string(),
  summary: z.string(),
  level,
  duration_minutes: z.number(),
  mode: z.enum(["OFFLINE", "HYBRID", "LIVE"]),
  pattern_ids: z.array(z.string()),
  lessons: z.array(z.string()),
});
export type LabSummary = z.output<typeof labSummarySchema>;

export const labSchema = labSummarySchema.extend({
  prerequisites: z.array(z.string()),
  steps: z.array(
    z.object({
      stage: z.string(),
      title: z.string(),
      instructions: z.string(),
      commands: z.array(z.string()),
      expected: z.string().nullable(),
      evidence_category: evidenceCategory.nullable(),
    }),
  ),
});
export type Lab = z.output<typeof labSchema>;

const levelTextSchema = z.object({
  executive: z.string(),
  l100: z.string(),
  l200: z.string(),
  l300: z.string(),
  l400: z.string(),
});
export const architectureSchema = z.object({
  layers: z.array(
    z.object({ id: z.string(), name: z.string(), question: z.string(), summary: z.string() }),
  ),
  components: z.array(
    z.object({
      id: z.string(),
      name: z.string(),
      layer: z.string(),
      status: capabilityStatus,
      description: levelTextSchema,
      owns: z.array(z.string()),
      does_not_own: z.array(z.string()),
      pattern_ids: z.array(z.string()),
      offline_equivalent: z.string(),
      sources: z.array(z.string()),
    }),
  ),
  flows: z.array(
    z.object({
      id: z.string(),
      source: z.string(),
      target: z.string(),
      label: z.string(),
      kind: z.enum([
        "context",
        "reasoning",
        "access",
        "authority",
        "evidence",
        "fallback",
        "change",
      ]),
    }),
  ),
});
export type ArchitectureMap = z.output<typeof architectureSchema>;
export type ArchitectureComponent = ArchitectureMap["components"][number];

export const completenessSchema = z.object({
  total: z.number(),
  answered: z.number(),
  coverage: z.number(),
  items: z.array(
    z.object({
      id: z.string(),
      question: z.string(),
      answered: z.boolean(),
      answered_by: z.array(z.string()),
      planned_phase: z.number().nullable(),
    }),
  ),
});
export type Completeness = z.output<typeof completenessSchema>;

// ------------------------------------------------------------------ architecture views (diagrams)
const nodeKind = z.enum([
  "person",
  "client",
  "harness",
  "knowledge",
  "app",
  "service",
  "foundry",
  "fabric",
  "data",
  "mcp",
  "gateway",
  "identity",
  "policy",
  "evidence",
  "local",
  "external",
]);
const nodeState = z.enum([
  "implemented",
  "planned",
  "documented",
  "preview",
  "tenant-validation",
  "optional",
]);
const runtimeBinding = z.enum([
  "api",
  "mcp",
  "fabric-local",
  "fabric-live",
  "foundry",
  "changes",
  "audit",
  "education",
  "evaluation",
  "router",
]);
const edgeKind = z.enum([
  "context",
  "reasoning",
  "access",
  "authority",
  "evidence",
  "fallback",
  "change",
  "data",
  "config",
]);
const boxSchema = z.object({ x: z.number(), y: z.number(), w: z.number(), h: z.number() });
const pointSchema = z.tuple([z.number(), z.number()]);

export const viewSummarySchema = z.object({
  id: z.string(),
  title: z.string(),
  kind: z.string(),
  summary: z.string(),
  doc: z.string().nullable(),
  pattern_ids: z.array(z.string()),
});
export type ViewSummary = z.output<typeof viewSummarySchema>;

export const diagramViewSchema = z.object({
  id: z.string(),
  title: z.string(),
  kind: z.enum(["reference", "system", "topology", "flow", "maturity", "resilience"]),
  summary: z.string(),
  cue: z.string(),
  aligned_to: z.array(z.string()),
  pattern_ids: z.array(z.string()),
  doc: z.string().nullable(),
  steps: z.array(z.object({ id: z.string(), label: z.string(), cue: z.string() })),
  zones: z.array(
    z.object({
      id: z.string(),
      label: z.string(),
      kind: z.enum(["local", "tenant", "fabric", "foundry", "github", "optional", "offline"]),
      step: z.string().nullable(),
    }),
  ),
  nodes: z.array(
    z.object({
      id: z.string(),
      label: z.string(),
      sublabel: z.string(),
      kind: nodeKind,
      state: nodeState,
      step: z.string().nullable(),
      component: z.string().nullable(),
      summary: z.string(),
      repo_path: z.string().nullable(),
      phase: z.number().nullable(),
      runtime: runtimeBinding.nullable(),
      sources: z.array(z.string()),
    }),
  ),
  edges: z.array(
    z.object({
      id: z.string(),
      source: z.string(),
      target: z.string(),
      label: z.string(),
      kind: edgeKind,
      step: z.string().nullable(),
      planned: z.boolean(),
    }),
  ),
  bands: z.array(
    z.object({
      id: z.string(),
      kind: z.enum(["identity", "policy", "evidence", "failure", "network"]),
      text: z.string(),
      step: z.string().nullable(),
    }),
  ),
  traces: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      summary: z.string(),
      label: z.enum(["PLANNED FLOW", "LOCAL", "SIMULATED", "PREVIEW", "DOCUMENTED"]),
      demo_act: z.number().nullable(),
      steps: z.array(
        z.object({
          node: z.string(),
          edge: z.string().nullable(),
          say: z.string(),
          note: z.string(),
        }),
      ),
    }),
  ),
});
export type DiagramView = z.output<typeof diagramViewSchema>;
export type DiagramNode = DiagramView["nodes"][number];
export type DiagramTrace = DiagramView["traces"][number];

export const viewLayoutSchema = z.object({
  width: z.number(),
  height: z.number(),
  grid_bottom: z.number(),
  nodes: z.record(z.string(), boxSchema),
  zones: z.record(z.string(), boxSchema),
  edges: z.record(
    z.string(),
    z.object({ points: z.array(pointSchema), label_at: pointSchema, label_fraction: z.number() }),
  ),
});
export type ViewLayout = z.output<typeof viewLayoutSchema>;

export const renderedViewSchema = z.object({ view: diagramViewSchema, layout: viewLayoutSchema });
export type RenderedView = z.output<typeof renderedViewSchema>;

export const viewRuntimeSchema = z.object({
  view_id: z.string(),
  operating_mode: operatingMode,
  observed_at: z.string(),
  nodes: z.array(
    z.object({
      node: z.string(),
      binding: runtimeBinding,
      status: z.enum(["ACTIVE", "READY", "DEGRADED", "UNAVAILABLE", "NOT CONFIGURED"]),
      label: z.string(),
      detail: z.string(),
    }),
  ),
});
export type ViewRuntime = z.output<typeof viewRuntimeSchema>;
export type NodeRuntime = ViewRuntime["nodes"][number];

// ------------------------------------------------------------------ agents
export const agentProfileSchema = z.object({
  agent: z.string(),
  suite: z.string(),
  dataset_profile: z.string(),
  local_provider: z.string(),
  live_provider: z.string().nullable(),
  suggested_questions: z.array(z.string()),
});
export type AgentProfile = z.output<typeof agentProfileSchema>;

export const agentAnswerSchema = z.object({
  agent: z.string(),
  question: z.string(),
  answer: z.string(),
  tool_calls: z.array(z.object({ name: z.string(), summary: z.string() })),
  grounded: z.boolean(),
  supported_questions: z.array(z.string()),
});
export type AgentAnswer = z.output<typeof agentAnswerSchema>;

export const agentEvalReportSchema = z.object({
  evaluation_id: z.string(),
  suite: z.string(),
  provider: z.string(),
  labels: z.array(z.string()),
  compared: z.number(),
  passed: z.number(),
  pass_rate: z.number(),
  gate_passed: z.boolean(),
  status: z.enum(["PASSED", "FAILED"]),
  cases: z.array(
    z.object({
      id: z.string(),
      question: z.string(),
      passed: z.boolean(),
      grounded: z.boolean(),
      missing: z.array(z.string()),
      label: z.string(),
      answer_excerpt: z.string(),
      tools: z.array(z.string()),
    }),
  ),
});
export type AgentEvalReport = z.output<typeof agentEvalReportSchema>;

export const monthlyInsightsRunSchema = z.object({
  run_id: z.string(),
  workflow: z.string(),
  engine: z.string(),
  dataset_profile: z.string(),
  observation_month: z.string(),
  steps: z.array(z.string()),
  drafts: z.array(
    z.object({
      team_id: z.string(),
      team_name: z.string(),
      question: z.string(),
      answer: z.string(),
      label: z.string(),
      provider: z.string(),
      fallback_used: z.boolean(),
      grounded: z.boolean(),
      expected: z.array(z.string()),
      missing: z.array(z.string()),
      status: z.enum(["READY FOR APPROVAL", "HELD"]),
      reason: z.string(),
      correlation_id: z.string(),
    }),
  ),
  ready: z.number(),
  held: z.number(),
  labels: z.array(z.string()),
  delivery: z.string(),
  synthetic_notice: z.string(),
});
export type MonthlyInsightsRun = z.output<typeof monthlyInsightsRunSchema>;

/** Compile-time drift detection between the backend contract and the UI's views. */
export const contractChecks = {
  runtimeStatus: true satisfies Conforms<G.RuntimeStatus, RuntimeStatus>,
  demoCheck: true satisfies Conforms<G.DemoCheckReport, DemoCheckReport>,
  offlineDemo: true satisfies Conforms<G.OfflineDemoReport, OfflineDemoReport>,
  pattern: true satisfies Conforms<G.ArchitecturePattern, Pattern>,
  recommendation: true satisfies Conforms<G.Recommendation, Recommendation>,
  selectionSignal: true satisfies Conforms<G.SelectionSignal, SelectionSignal>,
  guide: true satisfies Conforms<G.UseCaseGuide, Guide>,
  proposedChange: true satisfies Conforms<G.ProposedChange, ProposedChange>,
  approval: true satisfies Conforms<G.Approval, Approval>,
  executionResult: true satisfies Conforms<
    G.ExecutionResult,
    z.output<typeof executionResultSchema>
  >,
  auditRecord: true satisfies Conforms<G.AuditRecord, AuditRecord>,
  envelope: true satisfies Conforms<Omit<G.ExecutionEnvelope_object_, "data">, EnvelopeMeta>,
  workspace: true satisfies Conforms<G.WorkspaceInfo, z.output<typeof workspaceSchema>>,
  item: true satisfies Conforms<G.ItemInfo, z.output<typeof itemSchema>>,
  tableInfo: true satisfies Conforms<G.TableInfo, TableInfo>,
  tablePreview: true satisfies Conforms<G.TablePreview, TablePreview>,
  evaluation: true satisfies Conforms<G.EvaluationResult, EvaluationResult>,
  lessonSummary: true satisfies Conforms<G.LessonSummary, LessonSummary>,
  lesson: true satisfies Conforms<G.LessonView, Lesson>,
  checkGrade: true satisfies Conforms<G.CheckGrade, CheckGrade>,
  labSummary: true satisfies Conforms<G.LabSummary, LabSummary>,
  lab: true satisfies Conforms<G.Lab, Lab>,
  architecture: true satisfies Conforms<G.ArchitectureMap, ArchitectureMap>,
  completeness: true satisfies Conforms<G.CompletenessReport, Completeness>,
  viewSummary: true satisfies Conforms<G.ViewSummary, ViewSummary>,
  renderedView: true satisfies Conforms<G.RenderedView, RenderedView>,
  viewRuntime: true satisfies Conforms<G.ViewRuntime, ViewRuntime>,
  agentProfile: true satisfies Conforms<G.AgentProfile, AgentProfile>,
  agentAnswer: true satisfies Conforms<G.AgentAnswer, AgentAnswer>,
  agentEvalReport: true satisfies Conforms<G.AgentEvalReport, AgentEvalReport>,
  monthlyInsights: true satisfies Conforms<G.MonthlyInsightsRun, MonthlyInsightsRun>,
} as const;
