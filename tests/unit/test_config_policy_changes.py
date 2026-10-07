from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from tests.conftest import CONFIG_ROOT

from fabric_foundry_accelerator.audit.store import InMemoryAuditStore
from fabric_foundry_accelerator.config.environment import load_environment
from fabric_foundry_accelerator.config.overlay import CustomerOverlay, load_overlay
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.models.changes import (
    ApprovalDecision,
    ApprovalRequest,
    ChangeRequest,
    ChangeStatus,
    ExecuteRequest,
    FabricTarget,
)
from fabric_foundry_accelerator.models.execution import (
    EvidenceCategory,
    ExecutionLabel,
    OperatingMode,
)
from fabric_foundry_accelerator.policies.engine import (
    evaluate_write,
    load_tool_manifest,
    load_write_policy,
)
from fabric_foundry_accelerator.providers.errors import UnknownResourceError
from fabric_foundry_accelerator.services.changes import (
    ApprovalError,
    ChangeService,
    LiveWriteUnavailableError,
)


# ------------------------------------------------------------------ settings and configuration
def test_settings_treat_empty_paths_as_unset() -> None:
    settings = Settings(_env_file=None, audit_path="", output_root="")  # pyright: ignore[reportCallIssue]
    assert settings.audit_path is None
    assert settings.lakehouse_root == settings.data_root


def test_settings_read_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FFIA_ENVIRONMENT", "hybrid")
    monkeypatch.setenv("FFIA_SIMULATE_FABRIC_OUTAGE", "true")
    settings = Settings(_env_file=None)  # pyright: ignore[reportCallIssue]
    assert settings.environment == "hybrid" and settings.simulate_fabric_outage


@pytest.mark.parametrize(
    ("name", "mode"), [("offline", "OFFLINE"), ("hybrid", "HYBRID"), ("live", "LIVE")]
)
def test_environments_load(name: str, mode: str) -> None:
    environment = load_environment(CONFIG_ROOT, name)
    assert environment.mode.value == mode
    assert (
        environment.policy("knowledge").preferred == "local"
    )  # unconfigured capability defaults to local


def test_only_hybrid_falls_back_for_reads() -> None:
    assert load_environment(CONFIG_ROOT, "offline").policy("fabric_data").fallback == "none"
    assert load_environment(CONFIG_ROOT, "hybrid").policy("fabric_data").fallback == "local"
    assert load_environment(CONFIG_ROOT, "live").policy("fabric_data").fallback == "none"


def _overlay_fields() -> dict[str, object]:
    return load_overlay(CONFIG_ROOT, "example-healthcare").model_dump()


def test_example_overlay_is_synthetic_with_previews_off() -> None:
    overlay = load_overlay(CONFIG_ROOT, "example-healthcare")
    assert overlay.synthetic is True
    assert overlay.enabled_previews() == []
    assert overlay.approval_rule("create_lakehouse") is not None
    assert overlay.approval_rule("delete_item") is None


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"synthetic_dataset": "nope"}, "unknown synthetic_dataset"),
        ({"fabric_workspace_aliases": {"Bad_Alias": "x"}}, "aliases must be lowercase"),
        (
            {"allowed_writes": ["create_lakehouse"]},
            "approval rules for operations that are not allowed",
        ),
        ({"synthetic": False}, "synthetic"),
    ],
)
def test_overlay_validation(override: dict[str, object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        CustomerOverlay.model_validate({**_overlay_fields(), **override})


# ------------------------------------------------------------------ policy
def _decide(**overrides: object) -> tuple[bool, tuple[str, ...]]:
    arguments: dict[str, object] = {
        "operation": "create_lakehouse",
        "item_type": "Lakehouse",
        "destination": "LOCAL",
        "workspace_alias": "demo-dev",
        "allowed_writes": ("create_lakehouse",),
        "workspace_aliases": ("demo-dev",),
        "allow_live_mutation": False,
    }
    arguments.update(overrides)
    decision = evaluate_write(load_write_policy(CONFIG_ROOT), **arguments)  # pyright: ignore[reportArgumentType]
    assert decision.approval_required
    return decision.allowed, decision.reasons


@pytest.mark.parametrize(
    ("override", "fragment"),
    [
        ({"operation": "drop_everything"}, "Unknown operation"),
        ({"allowed_writes": ()}, "not in the overlay"),
        ({"item_type": "Report"}, "does not apply to item type"),
        ({"workspace_alias": "prod"}, "not declared in the overlay"),
        ({"destination": "LIVE"}, "Live mutation is disabled"),
    ],
)
def test_policy_denials(override: dict[str, object], fragment: str) -> None:
    allowed, reasons = _decide(**override)
    assert not allowed
    assert any(fragment in r for r in reasons)


def test_policy_allows_local_and_gated_live() -> None:
    assert _decide()[0]
    assert _decide(destination="LIVE", allow_live_mutation=True)[0]


def test_tool_manifest_has_no_approval_or_execution_tools() -> None:
    manifest = load_tool_manifest(CONFIG_ROOT)
    names = set(manifest.enabled())
    assert not {n for n in names if "approve" in n or "execute" in n}
    assert all(t.read_only or t.allowed_operations == ("propose",) for t in manifest.tools)


# ------------------------------------------------------------------ change flow
class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


def _service(
    *, allow_live: bool = False, clock: Callable[[], datetime] | None = None
) -> tuple[ChangeService, InMemoryAuditStore]:
    audit = InMemoryAuditStore()
    service = ChangeService(
        policy=load_write_policy(CONFIG_ROOT),
        overlay=load_overlay(CONFIG_ROOT, "example-healthcare"),
        audit=audit,
        mode=OperatingMode.OFFLINE,
        allow_live_mutation=allow_live,
        clock=clock or Clock(),
    )
    return service, audit


def _request(
    operation: str = "create_lakehouse",
    item_type: str = "Lakehouse",
    name: str = "lh",
    destination: str = "LOCAL",
) -> ChangeRequest:
    target = FabricTarget.model_validate(
        {
            "workspace_alias": "demo-dev",
            "item_type": item_type,
            "item_name": name,
            "destination": destination,
        }
    )
    return ChangeRequest(
        operation=operation, target=target, reason="unit test change", requested_by="alice"
    )


def _approve(service: ChangeService, change_id: str, approver: str = "bob") -> str:
    return service.approve(
        ApprovalRequest(change_id=change_id, approver=approver, decision=ApprovalDecision.APPROVED)
    ).approval_id


def test_full_local_flow_is_simulated_verified_and_audited() -> None:
    service, audit = _service()
    plan = service.plan(_request(), correlation_id="c" * 32)
    assert plan.status is ChangeStatus.PROPOSED and plan.precondition.passed
    approval_id = _approve(service, plan.change_id)
    envelope = service.execute(
        ExecuteRequest(change_id=plan.change_id, approval_id=approval_id, executed_by="writer")
    )
    assert envelope.execution_label is ExecutionLabel.SIMULATED
    assert envelope.cloud_operation_performed is False
    assert envelope.data.status is ChangeStatus.VERIFIED
    actions = [r.action for r in audit.for_correlation("c" * 32)]
    assert actions == ["change:plan", "change:approve:APPROVED", "change:execute"]
    assert service.get_plan(plan.change_id).status is ChangeStatus.VERIFIED
    assert len(service.plans()) == 1


def test_separation_of_duties_and_rejection() -> None:
    service, audit = _service()
    plan = service.plan(_request())
    with pytest.raises(ApprovalError, match="separation of duties"):
        _approve(service, plan.change_id, approver="ALICE")
    refused = audit.for_correlation(plan.correlation_id)[-1]
    assert (refused.action, refused.success, refused.actor) == (
        "change:approve:APPROVED",
        False,
        "ALICE",
    )
    rejection = service.approve(
        ApprovalRequest(
            change_id=plan.change_id, approver="bob", decision=ApprovalDecision.REJECTED
        )
    )
    assert service.get_plan(plan.change_id).status is ChangeStatus.REJECTED
    with pytest.raises(ApprovalError, match="only PROPOSED"):
        _approve(service, plan.change_id)
    with pytest.raises(ApprovalError, match="rejected"):
        service.execute(
            ExecuteRequest(
                change_id=plan.change_id, approval_id=rejection.approval_id, executed_by="w"
            )
        )


def test_approval_expires() -> None:
    clock = Clock()
    service, _ = _service(clock=clock)
    plan = service.plan(_request())
    approval_id = _approve(service, plan.change_id)
    clock.now += timedelta(minutes=31)
    with pytest.raises(ApprovalError, match="expired"):
        service.execute(
            ExecuteRequest(change_id=plan.change_id, approval_id=approval_id, executed_by="w")
        )


def test_approval_is_bound_to_its_change_and_executes_once() -> None:
    service, _ = _service()
    first, second = service.plan(_request(name="a")), service.plan(_request(name="b"))
    approval_id = _approve(service, first.change_id)
    with pytest.raises(ApprovalError, match="not found for this change"):
        service.execute(
            ExecuteRequest(change_id=second.change_id, approval_id=approval_id, executed_by="w")
        )
    service.execute(
        ExecuteRequest(change_id=first.change_id, approval_id=approval_id, executed_by="w")
    )
    with pytest.raises(ApprovalError, match="cannot execute again"):
        service.execute(
            ExecuteRequest(change_id=first.change_id, approval_id=approval_id, executed_by="w")
        )


def test_destination_hash_mismatch_is_refused() -> None:
    service, _ = _service()
    plan = service.plan(_request())
    approval_id = _approve(service, plan.change_id)
    tampered = plan.model_copy(
        update={
            "target": plan.target.model_copy(update={"item_name": "other"}),
            "status": ChangeStatus.APPROVED,
        }
    )
    # Simulates storage tampering between approval and execution.
    service._plans[plan.change_id] = tampered  # pyright: ignore[reportPrivateUsage]
    with pytest.raises(ApprovalError, match="different target"):
        service.execute(
            ExecuteRequest(change_id=plan.change_id, approval_id=approval_id, executed_by="w")
        )


def test_duplicates_are_blocked_and_preconditions_rechecked_at_execution() -> None:
    service, _ = _service()
    first, racing = service.plan(_request()), service.plan(_request())
    first_approval, racing_approval = (
        _approve(service, first.change_id),
        _approve(service, racing.change_id),
    )
    service.execute(
        ExecuteRequest(change_id=first.change_id, approval_id=first_approval, executed_by="w")
    )
    assert service.plan(_request()).status is ChangeStatus.BLOCKED
    with pytest.raises(ApprovalError, match="precondition failed at execution time"):
        service.execute(
            ExecuteRequest(change_id=racing.change_id, approval_id=racing_approval, executed_by="w")
        )
    assert service.get_plan(racing.change_id).status is ChangeStatus.FAILED


def test_updates_require_an_existing_target_and_delete_removes_it() -> None:
    service, _ = _service()
    assert service.plan(_request("upload_files")).status is ChangeStatus.BLOCKED
    service.workspace.apply("create_lakehouse", _request().target)
    upload = service.plan(_request("upload_files"))
    service.execute(
        ExecuteRequest(
            change_id=upload.change_id,
            approval_id=_approve(service, upload.change_id),
            executed_by="w",
        )
    )
    assert service.workspace.revision(_request().target) == 2
    policy = load_write_policy(CONFIG_ROOT)
    overlay = load_overlay(CONFIG_ROOT, "example-healthcare").model_copy(
        update={"allowed_writes": ("create_lakehouse", "delete_item")}
    )
    deleting = ChangeService(
        policy=policy,
        overlay=overlay,
        audit=InMemoryAuditStore(),
        mode=OperatingMode.OFFLINE,
        allow_live_mutation=False,
        workspace=service.workspace,
    )
    delete = deleting.plan(_request("delete_item"))
    assert delete.reversible is False and delete.risk == "high"
    result = deleting.execute(
        ExecuteRequest(
            change_id=delete.change_id,
            approval_id=_approve(deleting, delete.change_id),
            executed_by="w",
        )
    )
    assert result.data.verification.passed and not service.workspace.exists(_request().target)


def test_approved_live_change_is_never_redirected_to_local() -> None:
    service, audit = _service(allow_live=True)
    plan = service.plan(_request(destination="LIVE"))
    assert plan.status is ChangeStatus.PROPOSED
    assert plan.precondition.category is EvidenceCategory.REQUIRES_TENANT_VALIDATION
    approval_id = _approve(service, plan.change_id)
    with pytest.raises(LiveWriteUnavailableError, match="NOT redirected to LOCAL"):
        service.execute(
            ExecuteRequest(change_id=plan.change_id, approval_id=approval_id, executed_by="w")
        )
    assert service.workspace.items() == []
    assert service.get_plan(plan.change_id).status is ChangeStatus.APPROVED
    record = audit.recent()[-1]
    assert record.execution_label is ExecutionLabel.UNAVAILABLE and not record.success


def test_live_plans_are_blocked_without_the_mutation_flag() -> None:
    service, _ = _service()
    assert service.plan(_request(destination="LIVE")).status is ChangeStatus.BLOCKED


def test_unknown_plan_and_revalidate(tmp_path: Path) -> None:
    service, _ = _service()
    with pytest.raises(UnknownResourceError):
        service.get_plan("missing")
    plan = service.plan(_request())
    fresh = service.revalidate(plan.change_id)
    assert fresh.change_id == plan.change_id and len(service.plans()) == 1
