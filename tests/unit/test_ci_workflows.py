"""Release configuration keeps deterministic gates mandatory and cloud writes absent."""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("name", ["quality", "codeql", "release"])
def test_actions_are_immutable_and_checkout_has_no_persisted_credentials(name: str) -> None:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / f"{name}.yml").read_text())
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            action = step.get("uses", "")
            if action:
                assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", action), action
            if action.startswith("actions/checkout@"):
                assert step["with"]["persist-credentials"] is False
    assert workflow["permissions"]["contents"] == "read"


def test_release_requires_quality_and_codeql_and_only_uploads_artifacts() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())
    assert set(workflow["jobs"]["artifacts"]["needs"]) == {"quality", "codeql"}
    assert all(
        job.get("permissions", {}).get("contents", "read") == "read"
        for job in workflow["jobs"].values()
    )
    quality = yaml.safe_load((ROOT / ".github/workflows/quality.yml").read_text())
    assert quality["env"]["FFIA_ENVIRONMENT"] == "offline"
    assert quality["env"]["FFIA_FABRIC_LIVE"] == "0"
    assert quality["env"]["FFIA_FOUNDRY_LIVE"] == "0"
    commands = "\n".join(step.get("run", "") for step in quality["jobs"]["backend"]["steps"])
    for gate in (
        "ffia agents eval --suite sales-insights-agent",
        "ffia demo offline",
        "ffia prompts check",
        "ffia harness check",
        "ffia education check --min-coverage 1.0",
    ):
        assert gate in commands
    codeql = yaml.safe_load((ROOT / ".github/workflows/codeql.yml").read_text())
    assert set(codeql["jobs"]["analyze"]["strategy"]["matrix"]["language"]) == {
        "python",
        "javascript-typescript",
    }
