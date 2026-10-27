import { z } from "zod";
import { itemType } from "./common";

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
    fallback: z
      .object({
        server: z.string(),
        tools: z.array(z.string()),
        label: z.enum(["LOCAL", "SIMULATED"]),
        note: z.string(),
      })
      .nullable(),
  }),
  skills: z.array(z.string()),
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
