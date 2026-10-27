import { z } from "zod";
import { operatingMode, executionLabel, scalar } from "./common";

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
