import { z } from "zod";

export const level = z.enum(["executive", "l100", "l200", "l300", "l400"]);
export const capabilityStatus = z.enum([
  "GA",
  "PREVIEW",
  "MIXED",
  "DEPRECATED",
  "UNKNOWN/NEEDS VALIDATION",
  "LOCAL",
]);
export const operatingMode = z.enum(["LIVE", "HYBRID", "OFFLINE"]);
export const executionLabel = z.enum([
  "LIVE",
  "HYBRID",
  "LOCAL",
  "SIMULATED",
  "MOCKED",
  "PREVIEW",
  "UNAVAILABLE",
]);
export const evidenceCategory = z.enum([
  "SIMULATED LOCALLY",
  "DOCUMENTED FABRIC BEHAVIOR",
  "DOCUMENTED BEHAVIOR",
  "REQUIRES TENANT VALIDATION",
  "ASSUMPTION",
  "PRODUCTION RECOMMENDATION",
  "PREVIEW LIMITATION",
  "VERIFIED LIVE",
]);
export const changeStatus = z.enum([
  "PROPOSED",
  "BLOCKED",
  "APPROVED",
  "REJECTED",
  "EXECUTED",
  "VERIFIED",
  "FAILED",
]);
export const itemType = z.enum(["Lakehouse", "Notebook", "SemanticModel", "Report"]);
export const scalar = z.union([z.string(), z.number(), z.boolean(), z.null()]);
