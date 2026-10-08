import agentAnswer from "./fixtures/agent-answer.json";
import agentEval from "./fixtures/agent-eval.json";
import agentProfile from "./fixtures/agent-profile.json";
import agentUnsupported from "./fixtures/agent-unsupported.json";
import agentWorkflow from "./fixtures/agent-workflow.json";
import approval from "./fixtures/approval.json";
import architecture from "./fixtures/architecture.json";
import audit from "./fixtures/audit.json";
import checkGrade from "./fixtures/check-grade.json";
import completeness from "./fixtures/completeness.json";
import demoRun from "./fixtures/demo-run.json";
import demoStatus from "./fixtures/demo-status.json";
import evaluation from "./fixtures/evaluation.json";
import execution from "./fixtures/execution.json";
import guideHc01 from "./fixtures/guide-hc01.json";
import guides from "./fixtures/guides.json";
import labGovernedChange from "./fixtures/lab-governed-change.json";
import labs from "./fixtures/labs.json";
import lessonP08 from "./fixtures/lesson-p08.json";
import lessons from "./fixtures/lessons.json";
import patternP08 from "./fixtures/pattern-p08.json";
import patterns from "./fixtures/patterns.json";
import plan from "./fixtures/plan.json";
import profiles from "./fixtures/profiles.json";
import readItems from "./fixtures/read-items.json";
import readPreview from "./fixtures/read-preview.json";
import readTables from "./fixtures/read-tables.json";
import readWorkspaces from "./fixtures/read-workspaces.json";
import recommend from "./fixtures/recommend.json";
import runtimeStatus from "./fixtures/runtime-status.json";
import signals from "./fixtures/signals.json";
import viewHc01 from "./fixtures/view-hc01.json";
import viewReference from "./fixtures/view-reference.json";
import viewSystemRuntime from "./fixtures/view-system-runtime.json";
import viewSystem from "./fixtures/view-system.json";
import views from "./fixtures/views.json";
import type { Routes } from "./mockApi";

/** Real control-plane responses exported by `python -m tests.contract.export_frontend_fixtures`. */
export const fixtures = {
  agentAnswer,
  agentEval,
  agentProfile,
  agentUnsupported,
  agentWorkflow,
  approval,
  architecture,
  audit,
  checkGrade,
  completeness,
  demoRun,
  demoStatus,
  evaluation,
  execution,
  guideHc01,
  guides,
  labGovernedChange,
  labs,
  lessonP08,
  lessons,
  patternP08,
  patterns,
  plan,
  profiles,
  readItems,
  readPreview,
  readTables,
  readWorkspaces,
  recommend,
  runtimeStatus,
  signals,
  viewHc01,
  viewReference,
  viewSystem,
  viewSystemRuntime,
  views,
} as const;

const READS: Readonly<Record<string, unknown>> = {
  list_workspaces: readWorkspaces,
  list_items: readItems,
  list_tables: readTables,
  read_table: readPreview,
};

function readOperation(body: unknown): unknown {
  const operation =
    typeof body === "object" && body !== null && "operation" in body ? body.operation : null;
  return typeof operation === "string" ? READS[operation] : undefined;
}

/** Every route the app reads, answered with the exported fixtures. */
export const defaultRoutes: Routes = {
  "GET /api/v1/runtime/status": runtimeStatus,
  "GET /api/v1/demo/status": demoStatus,
  "POST /api/v1/demo/run": demoRun,
  "GET /api/v1/patterns": patterns,
  "GET /api/v1/patterns/P08": patternP08,
  "GET /api/v1/patterns/signals": signals,
  "POST /api/v1/patterns/recommend": recommend,
  "GET /api/v1/guides": guides,
  "GET /api/v1/guides/hc-01-fabric-mcp-powerbi-medallion-lab": guideHc01,
  "GET /api/v1/education/lessons": lessons,
  "GET /api/v1/education/lessons/p08-human-in-the-loop": lessonP08,
  "GET /api/v1/education/labs": labs,
  "GET /api/v1/education/labs/lab-governed-change": labGovernedChange,
  "GET /api/v1/education/architecture": architecture,
  "GET /api/v1/education/completeness": completeness,
  "GET /api/v1/profiles": profiles,
  "POST /api/v1/fabric/read": readOperation,
  "POST /api/v1/evaluations/run": evaluation,
  "POST /api/v1/plans": plan,
  "POST /api/v1/approvals": approval,
  "POST /api/v1/fabric/change": execution,
  [`GET /api/v1/audit/${plan.correlation_id}`]: audit,
  "GET /api/v1/education/views": views,
  "GET /api/v1/education/views/reference": viewReference,
  "GET /api/v1/education/views/system": viewSystem,
  "GET /api/v1/education/views/system/runtime": viewSystemRuntime,
  "GET /api/v1/education/views/hc-01": viewHc01,
  "GET /api/v1/agents/sales-insights-agent": agentProfile,
  "POST /api/v1/agents/ask": agentAnswer,
  "POST /api/v1/agents/evaluate": agentEval,
  "POST /api/v1/agents/workflows/monthly-insights": agentWorkflow,
};
