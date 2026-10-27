import { z } from "zod";
import type * as G from "../generated";
import type { RuntimeStatus, DemoCheckReport, OfflineDemoReport } from "./runtime";
import type { Pattern, Recommendation, SelectionSignal } from "./patterns";
import type { Guide } from "./guides";
import type { ProposedChange, Approval, executionResultSchema, AuditRecord } from "./changes";
import type {
  EnvelopeMeta,
  workspaceSchema,
  itemSchema,
  TableInfo,
  TablePreview,
  EvaluationResult,
} from "./fabric";
import type { LessonSummary, Workshop, Lesson, CheckGrade, LabSummary, Lab } from "./education";
import type {
  ArchitectureMap,
  Completeness,
  ViewSummary,
  RenderedView,
  ViewRuntime,
} from "./architecture";
import type { AgentProfile, AgentAnswer, AgentEvalReport, MonthlyInsightsRun } from "./agents";
import type { KnowledgeResult } from "./knowledge";
import type { BakeoffTasks, Scorecard, RunRecord } from "./bakeoff";

type DeepRequired<T> = T extends readonly [unknown, ...unknown[]]
  ? { -readonly [K in keyof T]: DeepRequired<T[K]> }
  : T extends readonly (infer U)[]
    ? DeepRequired<U>[]
    : T extends object
      ? { -readonly [K in keyof T]-?: DeepRequired<Exclude<T[K], undefined>> }
      : T;

/** `true` when every server response of type `Full` satisfies the UI view `View`. */
type Conforms<Full, View> = [DeepRequired<Full>] extends [View] ? true : never;

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
  workshop: true satisfies Conforms<G.WorkshopView, Workshop>,
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
  knowledge: true satisfies Conforms<G.KnowledgeResult, KnowledgeResult>,
  bakeoffTasks: true satisfies Conforms<G.TaskSet, BakeoffTasks>,
  scorecard: true satisfies Conforms<G.Scorecard, Scorecard>,
  runRecord: true satisfies Conforms<G.RunRecord, RunRecord>,
} as const;
