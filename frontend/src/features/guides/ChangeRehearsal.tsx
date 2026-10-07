import { useId, useState } from "react";
import type { Rehearsal } from "../../api/contracts";
import { describeError } from "../../api/client";
import { useApproveChange, useAudit, useExecuteChange, usePlanChange } from "../../api/hooks";
import { Badge } from "../../components/Badge";

/**
 * Rehearses a guide step's write through PLAN → APPROVE → EXECUTE → VERIFY → AUDIT against the
 * simulated workspace. Every rule (policy, duplicates, separation of duties) is enforced by the
 * backend; this component only shows what happened.
 */
export function ChangeRehearsal({
  rehearsal,
  stepTitle,
}: {
  readonly rehearsal: Rehearsal;
  readonly stepTitle: string;
}) {
  const [requestedBy, setRequestedBy] = useState("engineer-a");
  const [approver, setApprover] = useState("approver-b");
  const [workspaceAlias, setWorkspaceAlias] = useState("demo-dev");
  const plan = usePlanChange();
  const approve = useApproveChange();
  const execute = useExecuteChange();
  const audit = useAudit(plan.data?.correlation_id ?? null);
  const ids = { requester: useId(), approver: useId(), workspace: useId() };

  const reset = () => {
    plan.reset();
    approve.reset();
    execute.reset();
  };

  return (
    <section className="rehearsal" aria-labelledby="rehearsal-heading">
      <h3 id="rehearsal-heading">
        Rehearse this write <Badge value="SIMULATED" />
      </h3>
      <p>
        Runs <code>{rehearsal.operation}</code> on {rehearsal.item_type}{" "}
        <code>{rehearsal.item_name}</code> in the <strong>simulated</strong> workspace. No Fabric
        item is created. {rehearsal.note}
      </p>
      <div className="form-grid">
        <label htmlFor={ids.requester}>Requested by</label>
        <input
          id={ids.requester}
          value={requestedBy}
          onChange={(event) => {
            setRequestedBy(event.target.value);
          }}
        />
        <label htmlFor={ids.approver}>Approver</label>
        <input
          id={ids.approver}
          value={approver}
          onChange={(event) => {
            setApprover(event.target.value);
          }}
        />
        <label htmlFor={ids.workspace}>Workspace alias</label>
        <input
          id={ids.workspace}
          value={workspaceAlias}
          onChange={(event) => {
            setWorkspaceAlias(event.target.value);
          }}
        />
      </div>

      <ol className="flow">
        <li>
          <button
            type="button"
            disabled={plan.isPending}
            onClick={() => {
              reset();
              plan.mutate({
                rehearsal,
                workspaceAlias,
                requestedBy,
                reason: `Rehearsal of guide step: ${stepTitle}`,
              });
            }}
          >
            1. Plan and validate
          </button>
          {plan.error ? <p role="alert">{describeError(plan.error)}</p> : null}
          {plan.data ? (
            <div role="status" className="flow__result">
              <p>
                Plan <code>{plan.data.change_id}</code>:{" "}
                <Badge value={plan.data.status} kind="change" /> risk {plan.data.risk},{" "}
                {plan.data.reversible ? "reversible" : "not reversible"}.
              </p>
              <p>{plan.data.expected_impact}</p>
              <p>
                Precondition: {plan.data.precondition.name}:{" "}
                {plan.data.precondition.passed ? "passed" : "failed"}.{" "}
                {plan.data.precondition.detail}
              </p>
              <ul>
                {plan.data.policy_reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
              <p>Rollback: {plan.data.rollback}</p>
            </div>
          ) : null}
        </li>
        <li>
          <button
            type="button"
            disabled={plan.data?.status !== "PROPOSED" || approve.isPending || approve.isSuccess}
            onClick={() => {
              if (plan.data) {
                approve.mutate({ changeId: plan.data.change_id, approver });
              }
            }}
          >
            2. Approve as {approver || "approver"}
          </button>
          {approve.error ? (
            <p role="alert" className="result result--fail">
              Refused: {describeError(approve.error)}
            </p>
          ) : null}
          {approve.data ? (
            <p role="status">
              Approved by {approve.data.approver}; expires {approve.data.expires_at}.
            </p>
          ) : null}
        </li>
        <li>
          <button
            type="button"
            disabled={!approve.data || execute.isPending || execute.isSuccess}
            onClick={() => {
              if (plan.data && approve.data) {
                execute.mutate({
                  changeId: plan.data.change_id,
                  approvalId: approve.data.approval_id,
                });
              }
            }}
          >
            3. Execute with the scoped writer
          </button>
          {execute.error ? <p role="alert">{describeError(execute.error)}</p> : null}
          {execute.data ? (
            <div role="status" className="flow__result">
              <p>
                <Badge value={execute.data.execution_label} /> {execute.data.data.status}:{" "}
                {execute.data.data.verification.detail}
              </p>
              {execute.data.simulation_notice ? <p>{execute.data.simulation_notice}</p> : null}
            </div>
          ) : null}
        </li>
      </ol>

      {audit.data && audit.data.length > 0 ? (
        <details>
          <summary>Audit trail ({audit.data.length} records)</summary>
          <table>
            <caption className="visually-hidden">Audit records</caption>
            <thead>
              <tr>
                <th scope="col">Action</th>
                <th scope="col">Actor</th>
                <th scope="col">Label</th>
                <th scope="col">Success</th>
              </tr>
            </thead>
            <tbody>
              {audit.data.map((record) => (
                <tr key={record.audit_id}>
                  <td>{record.action}</td>
                  <td>{record.actor}</td>
                  <td>
                    <Badge value={record.execution_label} />
                  </td>
                  <td>{record.success ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      ) : null}
    </section>
  );
}
