import { z } from "zod";

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
  fallback_cases: z.number(),
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
      provider: z.string(),
      fallback_used: z.boolean(),
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
