import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import { api } from "./client";
import {
  agentAnswerSchema,
  agentEvalReportSchema,
  agentProfileSchema,
  approvalSchema,
  bakeoffTasksSchema,
  runRecordSchema,
  scorecardSchema,
  knowledgeResultSchema,
  monthlyInsightsRunSchema,
  architectureSchema,
  auditRecordSchema,
  checkGradeSchema,
  completenessSchema,
  demoCheckReportSchema,
  envelopeSchema,
  evaluationResultSchema,
  executionResultSchema,
  guideSchema,
  itemSchema,
  labSchema,
  labSummarySchema,
  lessonSchema,
  lessonSummarySchema,
  offlineDemoReportSchema,
  patternSchema,
  proposedChangeSchema,
  renderedViewSchema,
  recommendationSchema,
  runtimeStatusSchema,
  selectionSignalSchema,
  tableInfoSchema,
  tablePreviewSchema,
  viewRuntimeSchema,
  viewSummarySchema,
  workspaceSchema,
  type Rehearsal,
} from "./contracts";

const RUNTIME_REFRESH_MS = 15_000;

export function useRuntimeStatus() {
  return useQuery({
    queryKey: ["runtime-status"],
    queryFn: ({ signal }) => api.get("/api/v1/runtime/status", runtimeStatusSchema, signal),
    refetchInterval: RUNTIME_REFRESH_MS,
  });
}

export function useDemoStatus() {
  return useQuery({
    queryKey: ["demo-status"],
    queryFn: ({ signal }) => api.get("/api/v1/demo/status", demoCheckReportSchema, signal),
  });
}

export function useRunDemo() {
  return useMutation({
    mutationFn: () => api.post("/api/v1/demo/run", offlineDemoReportSchema, {}),
  });
}

export function usePatterns() {
  return useQuery({
    queryKey: ["patterns"],
    queryFn: ({ signal }) => api.get("/api/v1/patterns", z.array(patternSchema), signal),
  });
}

export function useSelectionSignals() {
  return useQuery({
    queryKey: ["selection-signals"],
    queryFn: ({ signal }) =>
      api.get("/api/v1/patterns/signals", z.array(selectionSignalSchema), signal),
  });
}

export function usePattern(patternId: string) {
  return useQuery({
    queryKey: ["pattern", patternId],
    queryFn: ({ signal }) =>
      api.get(`/api/v1/patterns/${encodeURIComponent(patternId)}`, patternSchema, signal),
  });
}

export function useRecommend() {
  return useMutation({
    mutationFn: (needs: readonly string[]) =>
      api.post("/api/v1/patterns/recommend", z.array(recommendationSchema), {
        needs,
        include_preview: true,
      }),
  });
}

export function useGuides() {
  return useQuery({
    queryKey: ["guides"],
    queryFn: ({ signal }) => api.get("/api/v1/guides", z.array(guideSchema), signal),
  });
}

export function useGuide(guideId: string) {
  return useQuery({
    queryKey: ["guide", guideId],
    queryFn: ({ signal }) =>
      api.get(`/api/v1/guides/${encodeURIComponent(guideId)}`, guideSchema, signal),
  });
}

export function useLessons() {
  return useQuery({
    queryKey: ["lessons"],
    queryFn: ({ signal }) =>
      api.get("/api/v1/education/lessons", z.array(lessonSummarySchema), signal),
  });
}

export function useLesson(lessonId: string) {
  return useQuery({
    queryKey: ["lesson", lessonId],
    queryFn: ({ signal }) =>
      api.get(`/api/v1/education/lessons/${encodeURIComponent(lessonId)}`, lessonSchema, signal),
  });
}

export function useAnswerCheck(lessonId: string, checkId: string) {
  return useMutation({
    mutationFn: (choice: number) =>
      api.post(
        `/api/v1/education/lessons/${encodeURIComponent(lessonId)}/checks/${encodeURIComponent(checkId)}`,
        checkGradeSchema,
        { choice },
      ),
  });
}

export function useLabs() {
  return useQuery({
    queryKey: ["labs"],
    queryFn: ({ signal }) => api.get("/api/v1/education/labs", z.array(labSummarySchema), signal),
  });
}

export function useLab(labId: string) {
  return useQuery({
    queryKey: ["lab", labId],
    queryFn: ({ signal }) =>
      api.get(`/api/v1/education/labs/${encodeURIComponent(labId)}`, labSchema, signal),
  });
}

export function useArchitecture() {
  return useQuery({
    queryKey: ["architecture"],
    queryFn: ({ signal }) => api.get("/api/v1/education/architecture", architectureSchema, signal),
  });
}

export function useViews() {
  return useQuery({
    queryKey: ["views"],
    queryFn: ({ signal }) => api.get("/api/v1/education/views", z.array(viewSummarySchema), signal),
  });
}

export function useView(viewId: string) {
  return useQuery({
    queryKey: ["view", viewId],
    queryFn: ({ signal }) =>
      api.get(`/api/v1/education/views/${encodeURIComponent(viewId)}`, renderedViewSchema, signal),
  });
}

/** Live node states for a view, refreshed while the overlay is on. */
export function useViewRuntime(viewId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["view-runtime", viewId],
    enabled,
    refetchInterval: enabled ? 10_000 : false,
    queryFn: ({ signal }) =>
      api.get(
        `/api/v1/education/views/${encodeURIComponent(viewId)}/runtime`,
        viewRuntimeSchema,
        signal,
      ),
  });
}

export function useCompleteness() {
  return useQuery({
    queryKey: ["completeness"],
    queryFn: ({ signal }) => api.get("/api/v1/education/completeness", completenessSchema, signal),
  });
}

/** Lakehouses visible through the Fabric read path (LOCAL offline). */
export function useLakehouses() {
  return useQuery({
    queryKey: ["lakehouses"],
    queryFn: async () => {
      const workspaces = await api.post(
        "/api/v1/fabric/read",
        envelopeSchema(z.array(workspaceSchema)),
        { operation: "list_workspaces" },
      );
      const items = await Promise.all(
        workspaces.data.map((workspace) =>
          api.post("/api/v1/fabric/read", envelopeSchema(z.array(itemSchema)), {
            operation: "list_items",
            workspace_id: workspace.id,
          }),
        ),
      );
      return items.flatMap((envelope) =>
        envelope.data
          .filter((item) => item.type === "Lakehouse")
          .map((item) => ({ ...item, label: envelope.execution_label })),
      );
    },
  });
}

export function useTables(lakehouseId: string | null) {
  return useQuery({
    queryKey: ["tables", lakehouseId],
    enabled: lakehouseId !== null,
    queryFn: () =>
      api.post("/api/v1/fabric/read", envelopeSchema(z.array(tableInfoSchema)), {
        operation: "list_tables",
        lakehouse_id: lakehouseId,
      }),
  });
}

export function usePreview(lakehouseId: string | null, table: string | null) {
  return useQuery({
    queryKey: ["preview", lakehouseId, table],
    enabled: lakehouseId !== null && table !== null,
    queryFn: () =>
      api.post("/api/v1/fabric/read", envelopeSchema(tablePreviewSchema), {
        operation: "read_table",
        lakehouse_id: lakehouseId,
        table,
        limit: 10,
      }),
  });
}

export function useEvaluation() {
  return useMutation({
    mutationFn: (profile: string) =>
      api.post("/api/v1/evaluations/run", envelopeSchema(evaluationResultSchema), {
        profile,
        observed_label: "LOCAL",
      }),
  });
}

export function useProfiles() {
  return useQuery({
    queryKey: ["profiles"],
    queryFn: ({ signal }) => api.get("/api/v1/profiles", z.array(z.string()), signal),
  });
}

// ------------------------------------------------------------------ governed change rehearsal
export interface PlanInput {
  readonly rehearsal: Rehearsal;
  readonly workspaceAlias: string;
  readonly requestedBy: string;
  readonly reason: string;
}

export function usePlanChange() {
  return useMutation({
    mutationFn: (input: PlanInput) =>
      api.post("/api/v1/plans", proposedChangeSchema, {
        operation: input.rehearsal.operation,
        target: {
          workspace_alias: input.workspaceAlias,
          item_type: input.rehearsal.item_type,
          item_name: input.rehearsal.item_name,
          destination: "LOCAL",
        },
        reason: input.reason,
        requested_by: input.requestedBy,
      }),
  });
}

export function useApproveChange() {
  return useMutation({
    mutationFn: (input: { readonly changeId: string; readonly approver: string }) =>
      api.post("/api/v1/approvals", approvalSchema, {
        change_id: input.changeId,
        approver: input.approver,
        decision: "APPROVED",
        comment: "Rehearsal approval",
      }),
  });
}

export function useExecuteChange() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { readonly changeId: string; readonly approvalId: string }) =>
      api.post("/api/v1/fabric/change", envelopeSchema(executionResultSchema), {
        change_id: input.changeId,
        approval_id: input.approvalId,
        executed_by: "scoped-writer",
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["audit"] }),
  });
}

export function useAudit(correlationId: string | null) {
  return useQuery({
    queryKey: ["audit", correlationId],
    enabled: correlationId !== null,
    queryFn: ({ signal }) =>
      api.get(
        `/api/v1/audit/${encodeURIComponent(correlationId ?? "")}`,
        z.array(auditRecordSchema),
        signal,
      ),
  });
}

export function useAgentProfile(agent: string) {
  return useQuery({
    queryKey: ["agent", agent],
    queryFn: ({ signal }) =>
      api.get(`/api/v1/agents/${encodeURIComponent(agent)}`, agentProfileSchema, signal),
  });
}

export function useAskAgent(agent: string) {
  return useMutation({
    mutationFn: (question: string) =>
      api.post("/api/v1/agents/ask", envelopeSchema(agentAnswerSchema), { agent, question }),
  });
}

export function useAgentEvaluation(suite: string) {
  return useMutation({
    mutationFn: () =>
      api.post(
        `/api/v1/agents/evaluate?suite=${encodeURIComponent(suite)}`,
        agentEvalReportSchema,
        undefined,
      ),
  });
}

export function useMonthlyInsights() {
  return useMutation({
    mutationFn: () =>
      api.post("/api/v1/agents/workflows/monthly-insights", monthlyInsightsRunSchema, {}),
  });
}

export function useKnowledgeSearch() {
  return useMutation({
    mutationFn: (question: string) =>
      api.post("/api/v1/knowledge/search", envelopeSchema(knowledgeResultSchema), {
        question,
        top: 3,
      }),
  });
}

export function useBakeoffTasks() {
  return useQuery({
    queryKey: ["bakeoff", "tasks"],
    queryFn: ({ signal }) => api.get("/api/v1/bakeoff/tasks", bakeoffTasksSchema, signal),
  });
}

export function useScorecard() {
  return useQuery({
    queryKey: ["bakeoff", "scorecard"],
    queryFn: ({ signal }) => api.get("/api/v1/bakeoff/scorecard", scorecardSchema, signal),
  });
}

export function useBakeoffRun(runId: string) {
  return useQuery({
    queryKey: ["bakeoff", "run", runId],
    queryFn: ({ signal }) =>
      api.get(`/api/v1/bakeoff/runs/${encodeURIComponent(runId)}`, runRecordSchema, signal),
  });
}
