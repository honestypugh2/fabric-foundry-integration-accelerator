"""The frontend's mocked API responses must stay valid against the backend contract."""

import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from fabric_foundry_accelerator.api.routes import SelectionSignal
from fabric_foundry_accelerator.audit.store import AuditRecord
from fabric_foundry_accelerator.education.guides import UseCaseGuide
from fabric_foundry_accelerator.education.lessons import ArchitectureMap, CompletenessReport, Lab
from fabric_foundry_accelerator.models.changes import Approval, ExecutionResult, ProposedChange
from fabric_foundry_accelerator.models.execution import ExecutionEnvelope
from fabric_foundry_accelerator.patterns.catalog import ArchitecturePattern, Recommendation
from fabric_foundry_accelerator.providers.fabric.port import (
    ItemInfo,
    TableInfo,
    TablePreview,
    WorkspaceInfo,
)
from fabric_foundry_accelerator.services.demo import DemoCheckReport, OfflineDemoReport
from fabric_foundry_accelerator.services.education import (
    CheckGrade,
    LabSummary,
    LessonSummary,
    LessonView,
)
from fabric_foundry_accelerator.services.evaluation import EvaluationResult
from fabric_foundry_accelerator.services.runtime import RuntimeStatus
from tests.conftest import REPO_ROOT

FIXTURES = REPO_ROOT / "frontend" / "src" / "test" / "fixtures"

CONTRACTS: dict[str, object] = {
    "runtime-status": RuntimeStatus,
    "demo-status": DemoCheckReport,
    "demo-run": OfflineDemoReport,
    "patterns": list[ArchitecturePattern],
    "pattern-p08": ArchitecturePattern,
    "recommend": list[Recommendation],
    "guides": list[UseCaseGuide],
    "guide-hc01": UseCaseGuide,
    "lessons": list[LessonSummary],
    "lesson-p08": LessonView,
    "check-grade": CheckGrade,
    "labs": list[LabSummary],
    "lab-governed-change": Lab,
    "architecture": ArchitectureMap,
    "completeness": CompletenessReport,
    "profiles": list[str],
    "signals": list[SelectionSignal],
    "read-workspaces": ExecutionEnvelope[list[WorkspaceInfo]],
    "read-items": ExecutionEnvelope[list[ItemInfo]],
    "read-tables": ExecutionEnvelope[list[TableInfo]],
    "read-preview": ExecutionEnvelope[TablePreview],
    "evaluation": ExecutionEnvelope[EvaluationResult],
    "plan": ProposedChange,
    "approval": Approval,
    "execution": ExecutionEnvelope[ExecutionResult],
    "audit": list[AuditRecord],
}


def test_every_fixture_has_a_contract() -> None:
    names = {path.stem for path in FIXTURES.glob("*.json")}
    assert names == set(CONTRACTS)


@pytest.mark.parametrize("name", sorted(CONTRACTS))
def test_fixture_matches_backend_model(name: str) -> None:
    payload: object = json.loads(Path(FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    TypeAdapter(CONTRACTS[name]).validate_python(payload)
