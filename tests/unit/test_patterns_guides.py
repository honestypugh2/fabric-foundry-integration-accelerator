from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from tests.conftest import REPO_ROOT

from fabric_foundry_accelerator.config.overlay import load_overlay
from fabric_foundry_accelerator.education.guides import (
    GuideStep,
    UseCaseGuide,
    load_guide,
    load_guides,
)
from fabric_foundry_accelerator.patterns.catalog import (
    SELECTION_SIGNALS,
    ArchitecturePattern,
    PatternCatalog,
    UnknownNeedError,
    load_catalog,
    recommend,
)
from fabric_foundry_accelerator.policies.engine import load_write_policy
from fabric_foundry_accelerator.research.sources import load_registry

HC_01 = "hc-01-fabric-mcp-powerbi-medallion-lab"


@pytest.fixture(scope="module")
def catalog() -> PatternCatalog:
    return load_catalog(REPO_ROOT / "education")


def test_catalog_has_24_patterns_with_valid_sources(catalog: PatternCatalog) -> None:
    assert [p.id for p in catalog.patterns] == [f"P{i:02d}" for i in range(1, 25)]
    assert (
        catalog.check_sources(load_registry(REPO_ROOT / "docs" / "research" / "sources.yaml")) == []
    )
    assert all(p.selection_signals for p in catalog.patterns)
    assert set(SELECTION_SIGNALS) == {s for p in catalog.patterns for s in p.selection_signals}


def test_recommendations_rank_and_filter(catalog: PatternCatalog) -> None:
    ranked = recommend(catalog, ["multiple-governed-domains", "shared-business-vocabulary"])
    assert ranked[0].pattern_id == "P02" and ranked[0].score == 2
    stable_only = recommend(catalog, ["shared-business-vocabulary"], include_preview=False)
    assert all(r.status != "PREVIEW" for r in stable_only)
    assert "Requires preview" in ranked[0].why
    with pytest.raises(UnknownNeedError, match="valid needs"):
        recommend(catalog, ["teleportation"])
    with pytest.raises(KeyError):
        catalog.get("P99")


def test_pattern_validation() -> None:
    base = load_catalog(REPO_ROOT / "education").get("P02").model_dump()
    with pytest.raises(ValidationError, match="unknown selection signals"):
        ArchitecturePattern.model_validate({**base, "selection_signals": ["nope"]})
    with pytest.raises(ValidationError, match="preview dependencies"):
        ArchitecturePattern.model_validate({**base, "preview_dependencies": []})


def test_hc01_guide_loads_with_safe_step_rules(catalog: PatternCatalog) -> None:
    guides = load_guides(REPO_ROOT / "guides", catalog)
    assert list(guides) == [HC_01, "mfg-01-foundry-fabric-sales-insights"]
    guide = guides[HC_01]
    assert guide.dataset_profile == "hc-lab-7file-v1"
    assert all(s.approval_required for s in guide.steps if s.writes)
    assert all(
        s.copilot_prompt and s.claude_code_prompt and s.offline_equivalent for s in guide.steps
    )
    # onelake_list-workspaces returned an empty list in a demo tenant; catalog search is reliable.
    assert guide.step("02-verify-tenant-anchor").tool_path.tools == (
        "core_search-catalog",
        "onelake_list-items",
    )
    assert not guide.step("02-verify-tenant-anchor").tool_path.substitution_allowed
    with pytest.raises(KeyError):
        guide.step("99-missing")
    assert (REPO_ROOT / guide.expected_baseline).is_file()


def test_hc01_rehearsals_are_allowed_by_policy_and_overlay() -> None:
    guide = load_guide(REPO_ROOT / "guides" / HC_01 / "guide.yaml")
    policy = load_write_policy(REPO_ROOT / "config")
    overlay = load_overlay(REPO_ROOT / "config", "example-healthcare")
    rehearsals = [s.rehearsal for s in guide.steps if s.rehearsal is not None]
    assert len(rehearsals) == 8
    for rehearsal in rehearsals:
        definition = policy.operation(rehearsal.operation)
        assert definition is not None and rehearsal.item_type in definition.item_types
        assert rehearsal.operation in overlay.allowed_writes
        assert overlay.approval_rule(rehearsal.operation) is not None


def test_template_is_valid_but_not_published() -> None:
    assert load_guide(REPO_ROOT / "guides" / "_template" / "guide.yaml").status == "draft"


def _write_guide(root: Path, folder: str, **overrides: object) -> None:
    data = yaml.safe_load(
        (REPO_ROOT / "guides" / "_template" / "guide.yaml").read_text(encoding="utf-8")
    )
    data.update({"id": folder, **overrides})
    (root / folder).mkdir(parents=True)
    (root / folder / "guide.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")


def test_guide_loader_rejects_mismatched_ids_and_unknown_patterns(
    tmp_path: Path, catalog: PatternCatalog
) -> None:
    _write_guide(tmp_path / "a", "fs-01-example")
    assert list(load_guides(tmp_path / "a", catalog)) == ["fs-01-example"]
    _write_guide(tmp_path / "b", "fs-02-example", patterns=["P99"])
    with pytest.raises(ValueError, match="unknown patterns"):
        load_guides(tmp_path / "b", catalog)
    _write_guide(tmp_path / "c", "fs-03-example")
    data = yaml.safe_load(
        (tmp_path / "c" / "fs-03-example" / "guide.yaml").read_text(encoding="utf-8")
    )
    data["id"] = "fs-04-other"
    (tmp_path / "c" / "fs-03-example" / "guide.yaml").write_text(
        yaml.safe_dump(data), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="must match its folder"):
        load_guides(tmp_path / "c", catalog)


def test_guide_model_rules() -> None:
    template = yaml.safe_load(
        (REPO_ROOT / "guides" / "_template" / "guide.yaml").read_text(encoding="utf-8")
    )
    step = template["steps"][0]
    with pytest.raises(ValidationError, match="must require approval"):
        GuideStep.model_validate({**step, "writes": True, "approval_required": False})
    rehearsal = {"operation": "create_lakehouse", "item_type": "Lakehouse", "item_name": "x"}
    with pytest.raises(ValidationError, match="only write steps can rehearse"):
        GuideStep.model_validate({**step, "writes": False, "rehearsal": rehearsal})
    with pytest.raises(ValidationError, match="unknown dataset_profile"):
        UseCaseGuide.model_validate({**template, "dataset_profile": "nope"})
    with pytest.raises(ValidationError, match="duplicate step ids"):
        UseCaseGuide.model_validate({**template, "steps": [step, step]})


def test_hc01_fabric_mcp_tools_are_allow_listed_in_its_profile(catalog: PatternCatalog) -> None:
    from fabric_foundry_accelerator.mcp.profiles import load_profiles  # noqa: PLC0415

    guide = load_guides(REPO_ROOT / "guides", catalog)[HC_01]
    allowed = set(
        load_profiles(REPO_ROOT / "config").profiles["hc01-lab"].servers["fabric-mcp"].tools
    )
    named = {
        t for s in guide.steps if s.tool_path.server == "fabric-mcp" for t in s.tool_path.tools
    }
    assert named and named <= allowed, named - allowed
