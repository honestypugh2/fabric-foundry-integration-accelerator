import io
from pathlib import Path

import pytest
import yaml

from fabric_foundry_accelerator import __version__
from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.privacy.leak_scan import hash_term

SALT = "unit-test-salt-0123456789"
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == __version__


def _make_repo(tmp_path: Path, content: str) -> Path:
    (tmp_path / "config" / "privacy").mkdir(parents=True)
    (tmp_path / "config" / "privacy" / "denylist.yaml").write_text(
        yaml.safe_dump({"version": 1, "salt": SALT, "hashes": [hash_term("contoso", SALT)]}),
        encoding="utf-8",
    )
    (tmp_path / "doc.md").write_text(content, encoding="utf-8")
    return tmp_path


def test_privacy_scan_clean_and_dirty(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    clean = _make_repo(tmp_path / "clean", "synthetic regional provider\n")
    assert main(["privacy", "scan", "--root", str(clean)]) == 0
    dirty = _make_repo(tmp_path / "dirty", "Contoso workspace\n")
    assert main(["privacy", "scan", "--root", str(dirty)]) == 1
    captured = capsys.readouterr()
    assert "[denylist]" in captured.err
    assert "contoso" not in captured.err.lower()


def test_privacy_scan_explicit_paths(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, "clean\n")
    assert main(["privacy", "scan", "--root", str(repo), str(repo / "doc.md")]) == 0


def test_privacy_add_terms_reads_stdin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _make_repo(tmp_path, "")
    denylist = repo / "config" / "privacy" / "denylist.yaml"
    monkeypatch.setattr("sys.stdin", io.StringIO("fabrikam\n\n"))
    assert main(["privacy", "add-terms", "--denylist", str(denylist)]) == 0
    assert "fabrikam" not in denylist.read_text(encoding="utf-8")


def test_sources_render_and_check(tmp_path: Path) -> None:
    output = tmp_path / "out.md"
    registry = str(REPO_ROOT / "docs" / "research" / "sources.yaml")
    assert main(["sources", "check", "--registry", registry, "--output", str(output)]) == 1
    assert main(["sources", "render", "--registry", registry, "--output", str(output)]) == 0
    assert main(["sources", "check", "--registry", registry, "--output", str(output)]) == 0
