"""Release SBOM validation rejects schema drift and incomplete runtime dependency inventories."""

import json
import shutil
from pathlib import Path

import pytest

from fabric_foundry_accelerator.sbom import main, normalize_npm_vcs_references, verify_sbom


@pytest.fixture
def sbom(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic.cdx.json"
    path.write_text(
        json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "version": 1,
                "components": [
                    {"type": "library", "name": "synthetic-package", "version": "1.0.0"}
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_valid_inventory_matches_normalized_exact_pins(sbom: Path) -> None:
    assert verify_sbom(sbom, {"Synthetic_Package": "1.0.0"}) == 1


@pytest.mark.parametrize("pins", [{"synthetic-package": "2.0.0"}, {"missing-package": "1.0.0"}])
def test_missing_or_wrong_runtime_pins_fail(sbom: Path, pins: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="missing exact runtime pins"):
        verify_sbom(sbom, pins)


def test_invalid_component_schema_fails(sbom: Path) -> None:
    data = json.loads(sbom.read_text(encoding="utf-8"))
    data["components"][0]["type"] = "not-a-component-type"
    sbom.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid CycloneDX schema"):
        verify_sbom(sbom, {"synthetic-package": "1.0.0"})


def test_npm_vcs_normalization_preserves_all_other_metadata(sbom: Path) -> None:
    data = json.loads(sbom.read_text(encoding="utf-8"))
    scp = "git@github.com:synthetic/example.git"  # leak-scan: allow - synthetic Git SSH URI
    ssh = "ssh://git@github.com/synthetic/example.git"  # leak-scan: allow - Git SSH URI
    references = [
        {"type": "vcs", "url": scp},
        {"type": "website", "url": "https://example.invalid"},
    ]
    data["components"][0]["externalReferences"] = references
    data["components"][0]["description"] = "Synthetic component"
    data["metadata"] = {"component": {"type": "application", "name": "synthetic-app"}}
    sbom.write_text(json.dumps(data), encoding="utf-8")
    assert normalize_npm_vcs_references(sbom) == 1
    references[0]["url"] = ssh
    assert json.loads(sbom.read_text(encoding="utf-8")) == data
    assert verify_sbom(sbom, {"synthetic-package": "1.0.0"}) == 1
    before = sbom.read_bytes()
    assert normalize_npm_vcs_references(sbom) == 0
    assert sbom.read_bytes() == before


def test_main_checks_both_manifests(
    sbom: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = sbom.parent
    (root / "sbom").mkdir()
    (root / "frontend").mkdir()
    for name in ("python", "frontend"):
        shutil.copyfile(sbom, root / "sbom" / f"{name}.cdx.json")
    project = root / "pyproject.toml"
    project.write_text(
        '[project]\ndependencies = ["synthetic-package[demo]==1.0.0"]\n', encoding="utf-8"
    )
    (root / "frontend" / "package.json").write_text(
        json.dumps({"dependencies": {"synthetic-package": "1.0.0"}}), encoding="utf-8"
    )
    monkeypatch.chdir(root)
    main()
    output = capsys.readouterr().out
    assert output.count("schema valid, 1 components, runtime pins matched") == 2
    assert output.count("LOCAL ") == 2
    project.write_text('[project]\ndependencies = ["synthetic-package"]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="runtime dependency is not exactly pinned"):
        main()
