"""Governed change flow: PLAN -> VALIDATE -> APPROVE -> EXECUTE -> VERIFY -> AUDIT.

Rules enforced here (not just documented):

* every write needs a plan, a policy decision and a human approval;
* the requester cannot approve their own change (separation of duties);
* approvals expire and are bound to the exact target via a destination hash;
* duplicates (creates) or missing targets (updates/deletes) are checked before approval and
  re-checked at execution time;
* LOCAL destinations execute against a simulated workspace and are labeled SIMULATED;
* an approved LIVE change is NEVER redirected to LOCAL: without an authorized live writer it
  returns UNAVAILABLE.
"""

from collections.abc import Callable
from datetime import datetime, timedelta

from fabric_foundry_accelerator.audit.store import AuditRecord, AuditStore, safe_details
from fabric_foundry_accelerator.config.overlay import CustomerOverlay
from fabric_foundry_accelerator.models.changes import (
    Approval,
    ApprovalDecision,
    ApprovalRequest,
    ChangeRequest,
    ChangeStatus,
    ExecuteRequest,
    ExecutionResult,
    FabricTarget,
    ProposedChange,
)
from fabric_foundry_accelerator.models.checks import CheckResult
from fabric_foundry_accelerator.models.execution import (
    EvidenceCategory,
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
    new_correlation_id,
    utc_now,
)
from fabric_foundry_accelerator.policies.engine import WritePolicy, evaluate_write
from fabric_foundry_accelerator.providers.errors import ProviderError, UnknownResourceError

CREATE_OPERATIONS = frozenset({"create_lakehouse", "create_notebook", "publish_report"})
SIMULATED_PROVIDER = "Simulated Workspace (LOCAL)"
SIMULATION_NOTICE = (
    "SIMULATED change against a local simulated workspace. No Microsoft Fabric item was created, "
    "changed or deleted."
)
ItemKey = tuple[str, str, str]


class ChangeError(ProviderError):
    """Base class for change-flow violations."""


class ApprovalError(ChangeError):
    """Raised when an approval or execution request violates the approval rules."""


class LiveWriteUnavailableError(ChangeError):
    """Raised when an approved LIVE change cannot execute. It is never redirected to LOCAL."""


class SimulatedWorkspace:
    """In-memory stand-in for workspace items, keyed by (alias, item type, item name)."""

    def __init__(self) -> None:
        """Create an empty simulated workspace."""
        self._revisions: dict[ItemKey, int] = {}

    @staticmethod
    def key(target: FabricTarget) -> ItemKey:
        """Return the item key for a target (names compare case-insensitively)."""
        return (target.workspace_alias, target.item_type, target.item_name.casefold())

    def exists(self, target: FabricTarget) -> bool:
        """Return True when the item exists."""
        return self.key(target) in self._revisions

    def revision(self, target: FabricTarget) -> int:
        """Return the item's revision (0 when absent)."""
        return self._revisions.get(self.key(target), 0)

    def apply(self, operation: str, target: FabricTarget) -> None:
        """Apply an operation."""
        key = self.key(target)
        if operation == "delete_item":
            self._revisions.pop(key, None)
        else:
            self._revisions[key] = self._revisions.get(key, 0) + 1

    def items(self) -> list[ItemKey]:
        """Return all item keys."""
        return sorted(self._revisions)


class ChangeService:
    """Plans, approves and executes changes under policy."""

    def __init__(
        self,
        *,
        policy: WritePolicy,
        overlay: CustomerOverlay,
        audit: AuditStore,
        mode: OperatingMode,
        allow_live_mutation: bool,
        workspace: SimulatedWorkspace | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        """Create the service. There is no live writer in this phase."""
        self._policy = policy
        self._overlay = overlay
        self._audit = audit
        self._mode = mode
        self._allow_live = allow_live_mutation
        self.workspace = workspace or SimulatedWorkspace()
        self._clock = clock
        self._plans: dict[str, ProposedChange] = {}
        self._approvals: dict[str, Approval] = {}

    # ------------------------------------------------------------------ plan
    def plan(self, request: ChangeRequest, *, correlation_id: str | None = None) -> ProposedChange:
        """Create and validate a plan. Nothing executes."""
        plan = self._evaluate(request, correlation_id or new_correlation_id())
        self._plans[plan.change_id] = plan
        self._record(
            plan,
            actor=request.requested_by,
            action="plan",
            success=plan.status is ChangeStatus.PROPOSED,
        )
        return plan

    def _evaluate(self, request: ChangeRequest, cid: str) -> ProposedChange:
        decision = evaluate_write(
            self._policy,
            operation=request.operation,
            item_type=request.target.item_type,
            destination=request.target.destination,
            workspace_alias=request.target.workspace_alias,
            allowed_writes=self._overlay.allowed_writes,
            workspace_aliases=tuple(self._overlay.fabric_workspace_aliases),
            allow_live_mutation=self._allow_live,
        )
        definition = self._policy.operation(request.operation)
        precondition = self._precondition(request.operation, request.target)
        blocked = not decision.allowed or (
            not precondition.passed and precondition.category is EvidenceCategory.SIMULATED_LOCALLY
        )
        return ProposedChange(
            correlation_id=cid,
            operation=request.operation,
            target=request.target,
            provider=SIMULATED_PROVIDER
            if request.target.destination == "LOCAL"
            else "Live Fabric writer (not available)",
            reason=request.reason,
            requested_by=request.requested_by,
            risk=decision.risk,
            reversible=definition.reversible if definition else False,
            expected_impact=definition.expected_impact if definition else "Unknown operation.",
            validation=definition.validation if definition else (),
            rollback=definition.rollback if definition else "Unknown operation.",
            approval_required=decision.approval_required,
            policy_allowed=decision.allowed,
            policy_reasons=decision.reasons,
            precondition=precondition,
            destination_hash=request.target.destination_hash(),
            status=ChangeStatus.BLOCKED if blocked else ChangeStatus.PROPOSED,
        )

    def _precondition(self, operation: str, target: FabricTarget) -> CheckResult:
        if target.destination == "LIVE":
            return CheckResult(
                name="Live workspace precondition",
                passed=False,
                detail=(
                    "Not verified: no live Fabric provider is configured. An authorized live writer must "
                    "re-check duplicates or existence immediately before executing."
                ),
                category=EvidenceCategory.REQUIRES_TENANT_VALIDATION,
            )
        exists = self.workspace.exists(target)
        if operation in CREATE_OPERATIONS:
            return CheckResult(
                name="No duplicate item exists",
                passed=not exists,
                detail=f"{target.item_type} {target.item_name!r} {'already exists' if exists else 'not found'} "
                f"in {target.workspace_alias} (simulated workspace)",
            )
        return CheckResult(
            name="Target item exists",
            passed=exists,
            detail=f"{target.item_type} {target.item_name!r} {'found' if exists else 'not found'} "
            f"in {target.workspace_alias} (simulated workspace)",
        )

    def get_plan(self, change_id: str) -> ProposedChange:
        """Return a plan or raise ``UnknownResourceError``."""
        try:
            return self._plans[change_id]
        except KeyError:
            raise UnknownResourceError(f"unknown change {change_id!r}") from None

    def plans(self) -> list[ProposedChange]:
        """Return all plans, oldest first."""
        return list(self._plans.values())

    def revalidate(self, change_id: str) -> ProposedChange:
        """Re-run policy and precondition checks for an existing plan (no state change)."""
        plan = self.get_plan(change_id)
        request = ChangeRequest(
            operation=plan.operation,
            target=plan.target,
            reason=plan.reason,
            requested_by=plan.requested_by,
        )
        fresh = self._evaluate(request, plan.correlation_id).model_copy(
            update={"change_id": plan.change_id, "created_at": plan.created_at}
        )
        self._record(
            fresh,
            actor=plan.requested_by,
            action="revalidate",
            success=fresh.status is ChangeStatus.PROPOSED,
        )
        return fresh

    # ------------------------------------------------------------------ approve
    def approve(self, request: ApprovalRequest) -> Approval:
        """Record a human approval or rejection."""
        plan = self.get_plan(request.change_id)
        if plan.status is not ChangeStatus.PROPOSED:
            raise ApprovalError(
                f"change {plan.change_id} is {plan.status}; only PROPOSED changes can be approved"
            )
        if (
            self._policy.separation_of_duties
            and request.approver.casefold() == plan.requested_by.casefold()
        ):
            raise ApprovalError(
                "separation of duties: the requester cannot approve their own change"
            )
        now = self._clock()
        approval = Approval(
            change_id=plan.change_id,
            approver=request.approver,
            decision=request.decision,
            comment=request.comment,
            destination_hash=plan.destination_hash,
            created_at=now,
            expires_at=now + timedelta(minutes=self._policy.approval_ttl_minutes),
        )
        self._approvals[approval.approval_id] = approval
        status = (
            ChangeStatus.APPROVED
            if request.decision is ApprovalDecision.APPROVED
            else ChangeStatus.REJECTED
        )
        self._plans[plan.change_id] = plan.model_copy(update={"status": status})
        self._record(
            plan,
            actor=request.approver,
            action=f"approve:{request.decision}",
            approval_id=approval.approval_id,
        )
        return approval

    # ------------------------------------------------------------------ execute
    def execute(self, request: ExecuteRequest) -> ExecutionEnvelope[ExecutionResult]:
        """Execute an approved change and verify it."""
        plan = self.get_plan(request.change_id)
        approval = self._valid_approval(plan, request.approval_id)
        if plan.target.destination == "LIVE":
            self._record(
                plan,
                actor=request.executed_by,
                action="execute",
                success=False,
                approval_id=approval.approval_id,
                label=ExecutionLabel.UNAVAILABLE,
                details={"outcome": "LIVE writer unavailable; NOT redirected to LOCAL"},
            )
            raise LiveWriteUnavailableError(
                "No authorized live Fabric writer is available. The approved LIVE change was NOT executed "
                "and was NOT redirected to LOCAL simulation. Re-plan once a live writer is configured."
            )
        precondition = self._precondition(plan.operation, plan.target)
        if not precondition.passed:
            self._plans[plan.change_id] = plan.model_copy(update={"status": ChangeStatus.FAILED})
            self._record(
                plan,
                actor=request.executed_by,
                action="execute",
                success=False,
                approval_id=approval.approval_id,
                details={
                    "outcome": f"precondition failed at execution time: {precondition.detail}"
                },
            )
            raise ApprovalError(f"precondition failed at execution time: {precondition.detail}")

        before = self.workspace.revision(plan.target)
        self.workspace.apply(plan.operation, plan.target)
        verification = self._verify(plan, before)
        status = ChangeStatus.VERIFIED if verification.passed else ChangeStatus.FAILED
        self._plans[plan.change_id] = plan.model_copy(update={"status": status})
        result = ExecutionResult(
            change_id=plan.change_id,
            approval_id=approval.approval_id,
            status=status,
            execution_label=ExecutionLabel.SIMULATED,
            verification=verification,
            rollback=plan.rollback,
        )
        self._record(
            plan,
            actor=request.executed_by,
            action="execute",
            success=verification.passed,
            approval_id=approval.approval_id,
            label=ExecutionLabel.SIMULATED,
        )
        return ExecutionEnvelope[ExecutionResult](
            operating_mode=self._mode,
            execution_label=ExecutionLabel.SIMULATED,
            requested_provider=SIMULATED_PROVIDER,
            selected_provider=SIMULATED_PROVIDER,
            cloud_operation_performed=False,
            equivalent_fabric_service=f"Fabric item operation: {plan.operation} ({plan.target.item_type})",
            teaching_objective=(
                "A model proposes, policy validates, a human approves, a scoped writer executes, "
                "then verify and audit."
            ),
            simulation_notice=SIMULATION_NOTICE,
            correlation_id=plan.correlation_id,
            data=result,
        )

    def _valid_approval(self, plan: ProposedChange, approval_id: str) -> Approval:
        approval = self._approvals.get(approval_id)
        if approval is None or approval.change_id != plan.change_id:
            raise ApprovalError("approval not found for this change")
        if approval.decision is not ApprovalDecision.APPROVED:
            raise ApprovalError("the change was rejected")
        if approval.is_expired(self._clock()):
            raise ApprovalError("the approval has expired; request a new approval")
        if approval.destination_hash != plan.target.destination_hash():
            raise ApprovalError("the approval was granted for a different target or destination")
        if plan.status is not ChangeStatus.APPROVED:
            raise ApprovalError(
                f"change {plan.change_id} is {plan.status}; it cannot execute again"
            )
        return approval

    def _verify(self, plan: ProposedChange, before: int) -> CheckResult:
        if plan.operation == "delete_item":
            passed = not self.workspace.exists(plan.target)
            detail = "item no longer present" if passed else "item still present"
        else:
            after = self.workspace.revision(plan.target)
            passed = after == before + 1
            detail = f"revision {before} -> {after}"
        return CheckResult(
            name=f"Verify {plan.operation} took effect", passed=passed, detail=detail
        )

    def _record(
        self,
        plan: ProposedChange,
        *,
        actor: str,
        action: str,
        success: bool = True,
        approval_id: str | None = None,
        label: ExecutionLabel = ExecutionLabel.LOCAL,
        details: dict[str, object] | None = None,
    ) -> None:
        base: dict[str, object] = {
            "operation": plan.operation,
            "destination": plan.target.destination,
            "item_type": plan.target.item_type,
            "item_name": plan.target.item_name,
            "workspace_alias": plan.target.workspace_alias,
            "risk": plan.risk,
        }
        base.update(details or {})
        self._audit.record(
            AuditRecord(
                correlation_id=plan.correlation_id,
                actor=actor,
                action=f"change:{action}",
                capability="fabric_change",
                requested_provider=plan.provider,
                selected_provider=plan.provider,
                operating_mode=self._mode,
                execution_label=label,
                cloud_operation_performed=False,
                success=success,
                change_id=plan.change_id,
                approval_id=approval_id,
                details=safe_details(base),
            )
        )
