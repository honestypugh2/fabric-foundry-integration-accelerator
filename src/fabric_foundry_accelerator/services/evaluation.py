"""Deterministic evaluation: compare measure values with the committed expected baseline.

Use it to prove that a live Fabric/Power BI run produced the right numbers. When values are
supplied by the caller (for example copied from DAX query results), the result says so: the
accelerator did not retrieve them itself.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.config.overlay import EvaluationThresholds
from fabric_foundry_accelerator.models.execution import (
    Evidence,
    EvidenceCategory,
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
    new_correlation_id,
)
from fabric_foundry_accelerator.providers.errors import UnknownResourceError
from fabric_foundry_accelerator.providers.fabric.port import FabricProvider
from fabric_foundry_accelerator.synthetic.baseline import load_baseline
from fabric_foundry_accelerator.synthetic.paths import expected_baseline_path
from fabric_foundry_accelerator.synthetic.profiles import PROFILES

MeasureInput = int | float | None


class EvaluationRequest(BaseModel):
    """Evaluate observed measure values (or the local provider's values) against the baseline."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile: str
    observed: dict[str, MeasureInput] | None = None
    observed_label: Literal["LIVE", "HYBRID", "LOCAL", "MOCKED"] = "LIVE"


class MeasureComparison(BaseModel):
    """One measure compared with its expected value."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    expected: MeasureInput
    observed: MeasureInput
    absolute_difference: float | None
    passed: bool


class EvaluationResult(BaseModel):
    """Outcome of an evaluation run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluation_id: str = Field(default_factory=new_correlation_id)
    profile: str
    observed_values_source: Literal["local-provider", "caller-supplied"]
    observed_label: str
    tolerance: float
    compared: int
    passed: int
    pass_rate: float
    gate_passed: bool
    comparisons: tuple[MeasureComparison, ...]
    missing_measures: tuple[str, ...]
    unexpected_measures: tuple[str, ...]


def compare(
    name: str, expected: MeasureInput, observed: MeasureInput, tolerance: float
) -> MeasureComparison:
    """Compare two values with an absolute tolerance (None equals only None)."""
    if expected is None or observed is None:
        return MeasureComparison(
            name=name,
            expected=expected,
            observed=observed,
            absolute_difference=None,
            passed=expected is None and observed is None,
        )
    difference = abs(float(expected) - float(observed))
    return MeasureComparison(
        name=name,
        expected=expected,
        observed=observed,
        absolute_difference=round(difference, 9),
        passed=difference <= tolerance,
    )


class EvaluationService:
    """Runs baseline evaluations."""

    def __init__(
        self,
        *,
        data_root: Path,
        fabric: FabricProvider,
        thresholds: EvaluationThresholds,
        mode: OperatingMode,
    ) -> None:
        """Create the service."""
        self._data_root = data_root
        self._fabric = fabric
        self._thresholds = thresholds
        self._mode = mode

    async def run(
        self, request: EvaluationRequest, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[EvaluationResult]:
        """Evaluate and return a LOCAL envelope (the comparison itself always runs locally)."""
        if request.profile not in PROFILES:
            raise UnknownResourceError(f"unknown profile {request.profile!r}")
        baseline = load_baseline(expected_baseline_path(self._data_root, request.profile))
        if request.observed is None:
            values = await self._fabric.evaluate_measures(
                f"local-sm-{request.profile}", correlation_id=correlation_id
            )
            observed: dict[str, MeasureInput] = {v.name: v.value for v in values.data}
            source: Literal["local-provider", "caller-supplied"] = "local-provider"
            label = values.execution_label.value
        else:
            observed, source, label = (
                dict(request.observed),
                "caller-supplied",
                request.observed_label,
            )
        tolerance = self._thresholds.measure_absolute_tolerance
        comparisons = tuple(
            compare(name, baseline.measures[name], observed[name], tolerance)
            for name in sorted(baseline.measures)
            if name in observed
        )
        passed = sum(c.passed for c in comparisons)
        rate = passed / len(comparisons) if comparisons else 0.0
        missing = tuple(sorted(set(baseline.measures) - set(observed)))
        result = EvaluationResult(
            profile=request.profile,
            observed_values_source=source,
            observed_label=label,
            tolerance=tolerance,
            compared=len(comparisons),
            passed=passed,
            pass_rate=round(rate, 6),
            gate_passed=bool(comparisons) and rate >= self._thresholds.minimum_pass_rate,
            comparisons=comparisons,
            missing_measures=missing,
            unexpected_measures=tuple(sorted(set(observed) - set(baseline.measures))),
        )
        evidence = (
            Evidence(
                category=EvidenceCategory.SIMULATED_LOCALLY
                if source == "local-provider"
                else EvidenceCategory.REQUIRES_TENANT_VALIDATION,
                statement=(
                    "Observed values came from the Local Fabric Provider."
                    if source == "local-provider"
                    else (
                        f"Observed values were supplied by the caller and labeled {label}; "
                        "the accelerator did not retrieve them."
                    )
                ),
            ),
        )
        return ExecutionEnvelope[EvaluationResult](
            operating_mode=self._mode,
            execution_label=ExecutionLabel.LOCAL,
            requested_provider="Baseline Evaluator",
            selected_provider="Baseline Evaluator",
            cloud_operation_performed=False,
            equivalent_fabric_service=(
                "Measure validation against expected results (Foundry evaluation / CI quality gate)"
            ),
            teaching_objective="Prove numbers, not appearance: compare every measure with the expected baseline.",
            simulation_notice="Evaluation computed locally from committed expected results.",
            correlation_id=correlation_id or new_correlation_id(),
            evidence=evidence,
            data=result,
        )
