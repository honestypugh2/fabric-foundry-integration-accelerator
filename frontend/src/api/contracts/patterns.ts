import { z } from "zod";

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
