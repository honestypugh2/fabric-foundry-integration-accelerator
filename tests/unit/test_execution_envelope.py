import pytest
from pydantic import ValidationError

from fabric_foundry_accelerator.models.execution import (
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
    new_correlation_id,
)


def _envelope(**overrides: object) -> ExecutionEnvelope[int]:
    fields: dict[str, object] = {
        "operating_mode": OperatingMode.OFFLINE,
        "execution_label": ExecutionLabel.LOCAL,
        "requested_provider": "p",
        "selected_provider": "p",
        "cloud_operation_performed": False,
        "equivalent_fabric_service": "Fabric Lakehouse",
        "teaching_objective": "t",
        "simulation_notice": "local only",
        "data": 1,
    }
    fields.update(overrides)
    return ExecutionEnvelope[int].model_validate(fields)


def test_valid_local_envelope_has_correlation_id_and_utc_timestamp() -> None:
    envelope = _envelope()
    assert len(envelope.correlation_id) == 32
    assert envelope.timestamp.utcoffset() is not None


@pytest.mark.parametrize(
    "label", [ExecutionLabel.LOCAL, ExecutionLabel.SIMULATED, ExecutionLabel.MOCKED]
)
def test_simulated_labels_can_never_claim_a_cloud_operation(label: ExecutionLabel) -> None:
    with pytest.raises(ValidationError, match="cannot claim a cloud operation"):
        _envelope(execution_label=label, cloud_operation_performed=True)


def test_simulated_labels_require_a_notice() -> None:
    with pytest.raises(ValidationError, match="simulation_notice"):
        _envelope(simulation_notice=None)


def test_live_label_must_report_a_cloud_operation_and_not_be_offline() -> None:
    with pytest.raises(ValidationError, match="cloud_operation_performed=True"):
        _envelope(execution_label=ExecutionLabel.LIVE, operating_mode=OperatingMode.LIVE)
    with pytest.raises(ValidationError, match="OFFLINE"):
        _envelope(execution_label=ExecutionLabel.LIVE, cloud_operation_performed=True)
    live = _envelope(
        execution_label=ExecutionLabel.LIVE,
        operating_mode=OperatingMode.LIVE,
        cloud_operation_performed=True,
        simulation_notice=None,
    )
    assert live.cloud_operation_performed


def test_fallback_requires_reason() -> None:
    with pytest.raises(ValidationError, match="fallback_reason"):
        _envelope(fallback_used=True)
    assert _envelope(fallback_used=True, fallback_reason="Fabric probe timed out").fallback_used


def test_correlation_id_format_is_enforced() -> None:
    assert len(new_correlation_id()) == 32
    with pytest.raises(ValidationError):
        _envelope(correlation_id="not-a-hex-id")
