import { z } from "zod";

export const bakeoffTasksSchema = z.object({
  profile: z.string(),
  tasks: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      summary: z.string(),
      allowed_changes: z.array(z.string()),
      checks: z.array(z.string()),
      prompt: z.string(),
    }),
  ),
});
export type BakeoffTasks = z.output<typeof bakeoffTasksSchema>;

const gradeReportSchema = z.object({
  task: z.string(),
  commit: z.string(),
  checks: z.array(z.object({ name: z.string(), passed: z.boolean(), detail: z.string() })),
  changed_files: z.array(z.string()),
  passed: z.boolean(),
});

export const scorecardSchema = z.object({
  label: z.enum(["LIVE", "UNAVAILABLE"]),
  note: z.string(),
  task_ids: z.array(z.string()),
  rows: z.array(
    z.object({
      harness: z.string(),
      model: z.string(),
      runs: z.number(),
      tasks_passed: z.number(),
      median_duration_seconds: z.number(),
      approvals_requested: z.number(),
      denied_tool_calls: z.number(),
      unsafe_attempts: z.number(),
      premium_requests: z.number().nullable(),
    }),
  ),
  runs: z.array(
    z.object({
      run_id: z.string(),
      recorded_on: z.string(),
      harness: z.string(),
      model: z.string(),
      task: z.string(),
      passed: z.boolean(),
      checks_passed: z.number(),
      checks: z.number(),
      duration_seconds: z.number(),
      current_prompt: z.boolean(),
    }),
  ),
});
export type Scorecard = z.output<typeof scorecardSchema>;

export const runRecordSchema = z.object({
  run_id: z.string(),
  recorded_on: z.string(),
  label: z.literal("LIVE"),
  harness: z.object({ name: z.string(), version: z.string() }),
  model: z.string(),
  task: z.string(),
  duration_seconds: z.number(),
  grade: gradeReportSchema,
  safety: z.object({
    approvals_requested: z.number(),
    denied_tool_calls: z.number(),
    unsafe_attempts: z.number(),
  }),
  usage: z.object({
    premium_requests: z.number().nullable(),
    input_tokens: z.number().nullable(),
    output_tokens: z.number().nullable(),
  }),
  transcript: z.array(
    z.object({
      t: z.number(),
      kind: z.enum([
        "prompt",
        "message",
        "tool_call",
        "tool_result",
        "approval_requested",
        "denied",
        "command",
      ]),
      name: z.string().nullable(),
      summary: z.string(),
    }),
  ),
  notes: z.string(),
});
export type RunRecord = z.output<typeof runRecordSchema>;
