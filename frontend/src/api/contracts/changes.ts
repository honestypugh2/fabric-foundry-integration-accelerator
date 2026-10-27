import { z } from "zod";
import { executionLabel, evidenceCategory, changeStatus, itemType } from "./common";

const fabricTargetSchema = z.object({
  workspace_alias: z.string(),
  item_type: itemType,
  item_name: z.string(),
  destination: z.enum(["LOCAL", "LIVE"]),
});
const checkResultSchema = z.object({
  name: z.string(),
  passed: z.boolean(),
  detail: z.string(),
  category: evidenceCategory,
});

export const proposedChangeSchema = z.object({
  change_id: z.string(),
  correlation_id: z.string(),
  operation: z.string(),
  target: fabricTargetSchema,
  provider: z.string(),
  reason: z.string(),
  requested_by: z.string(),
  risk: z.enum(["low", "medium", "high"]),
  reversible: z.boolean(),
  expected_impact: z.string(),
  validation: z.array(z.string()),
  rollback: z.string(),
  approval_required: z.boolean(),
  policy_allowed: z.boolean(),
  policy_reasons: z.array(z.string()),
  precondition: checkResultSchema,
  status: changeStatus,
});
export type ProposedChange = z.output<typeof proposedChangeSchema>;

export const approvalSchema = z.object({
  approval_id: z.string(),
  change_id: z.string(),
  approver: z.string(),
  decision: z.enum(["APPROVED", "REJECTED"]),
  expires_at: z.string(),
});
export type Approval = z.output<typeof approvalSchema>;

export const executionResultSchema = z.object({
  change_id: z.string(),
  approval_id: z.string(),
  status: changeStatus,
  execution_label: executionLabel,
  verification: checkResultSchema,
  rollback: z.string(),
});

export const auditRecordSchema = z.object({
  audit_id: z.string(),
  correlation_id: z.string(),
  timestamp: z.string(),
  actor: z.string(),
  action: z.string(),
  capability: z.string(),
  selected_provider: z.string(),
  execution_label: executionLabel,
  cloud_operation_performed: z.boolean(),
  success: z.boolean(),
});
export type AuditRecord = z.output<typeof auditRecordSchema>;
