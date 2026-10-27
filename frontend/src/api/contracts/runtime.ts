import { z } from "zod";
import { operatingMode } from "./common";

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
