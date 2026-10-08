"""Pinned, curated skills: hash verification, allow-listed extraction and offline checks."""

import hashlib
import io
import json
import shutil
import tarfile
from pathlib import Path

import httpx
import pytest
from tests.conftest import CONFIG_ROOT, REPO_ROOT

from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.skills import commands as skills_commands
from fabric_foundry_accelerator.skills.vendor import (
    AZ_REST_RULE,
    PIN_FILE,
    SkillsError,
    SkillsLock,
    check,
    download,
    extract,
    install,
    load_lock,
    status,
    verify_archive,
)

PREFIX = "skills-for-fabric-0.3.18"


def _archive(extra: dict[str, bytes] | None = None, *, link: bool = False) -> bytes:
    files = {
        f"{PREFIX}/skills/spark-cli/SKILL.md": b"---\nname: spark-cli\n---\n",
        f"{PREFIX}/skills/spark-cli/references/a.md": b"ref",
        f"{PREFIX}/skills/not-curated/SKILL.md": b"x",
        f"{PREFIX}/common/COMMON-CORE.md": b"core",
        f"{PREFIX}/.mcp.json": b'{"mcpServers": {"x": {"tools": ["*"]}}}',
        f"{PREFIX}/agents/persona.md": b"persona",
        **(extra or {}),
    }
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        if link:
            info = tarfile.TarInfo(f"{PREFIX}/skills/spark-cli/evil")
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            archive.addfile(info)
    return buffer.getvalue()


def _lock(data: bytes, **overrides: object) -> SkillsLock:
    base = load_lock(CONFIG_ROOT).model_dump()
    base.update(
        {
            "sha256": hashlib.sha256(data).hexdigest(),
            "skills": [{"name": "spark-cli", "why": "test"}],
            "support_dirs": ["common"],
            **overrides,
        }
    )
    return SkillsLock.model_validate(base)


def test_committed_lock_is_pinned_and_curated() -> None:
    lock = load_lock(CONFIG_ROOT)
    assert lock.tag == "v0.3.18" and lock.license == "MIT"
    assert [s.name for s in lock.skills] == [
        "e2e-medallion-architecture",
        "spark-cli",
        "semantic-model-authoring",
        "powerbi-report-cli",
    ]
    assert lock.archive_url.endswith(f"/refs/tags/{lock.tag}")


def test_committed_repository_passes_offline_check() -> None:
    assert check(load_lock(CONFIG_ROOT), REPO_ROOT) == []


def test_extract_writes_only_curated_files(tmp_path: Path) -> None:
    data = _archive(link=True)
    lock = _lock(data)
    written = extract(lock, data, tmp_path)
    relative = sorted(p.relative_to(tmp_path).as_posix() for p in written)
    assert relative == [
        ".claude/common/COMMON-CORE.md",
        ".claude/skills/spark-cli/SKILL.md",
        ".claude/skills/spark-cli/references/a.md",
    ]
    assert not (tmp_path / ".claude" / ".mcp.json").exists()
    assert not (tmp_path / ".claude" / "skills" / "spark-cli" / "evil").exists()
    pin = (tmp_path / ".claude" / "skills" / "spark-cli" / PIN_FILE).read_text(encoding="utf-8")
    assert pin.startswith("microsoft/skills-for-fabric@v0.3.18 sha256:")
    assert status(lock, tmp_path) == {"spark-cli": "installed (v0.3.18)"}


def test_reinstall_replaces_stale_files(tmp_path: Path) -> None:
    data = _archive()
    lock = _lock(data)
    stale = tmp_path / ".claude" / "skills" / "spark-cli" / "old.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("old", encoding="utf-8")
    extract(lock, data, tmp_path)
    assert not stale.exists()


@pytest.mark.parametrize("name", ["/abs/path", f"{PREFIX}/../escape"])
def test_unsafe_paths_are_refused(tmp_path: Path, name: str) -> None:
    data = _archive({name: b"x"})
    with pytest.raises(SkillsError, match="unsafe path"):
        extract(_lock(data), data, tmp_path)


def test_missing_skill_and_hash_mismatch(tmp_path: Path) -> None:
    data = _archive()
    with pytest.raises(SkillsError, match="not in microsoft/skills-for-fabric"):
        extract(_lock(data, skills=[{"name": "fabriciq", "why": "x"}]), data, tmp_path)
    with pytest.raises(SkillsError, match="does not match the pinned"):
        verify_archive(_lock(data, sha256="0" * 64), data)


def test_status_reports_missing_and_stale(tmp_path: Path) -> None:
    lock = _lock(_archive())
    assert status(lock, tmp_path) == {"spark-cli": "missing"}
    pin = tmp_path / ".claude" / "skills" / "spark-cli" / PIN_FILE
    pin.parent.mkdir(parents=True)
    pin.write_text("microsoft/skills-for-fabric@v0.3.17 sha256:x", encoding="utf-8")
    assert status(lock, tmp_path) == {"spark-cli": "stale pin"}


def _mock_client(data: bytes, status_code: int = 200) -> httpx.Client:
    return httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(status_code, content=data))
    )


def test_install_downloads_verifies_and_extracts(tmp_path: Path) -> None:
    data = _archive()
    lock = _lock(data)
    assert len(install(lock, tmp_path, _mock_client(data))) == 3
    with pytest.raises(SkillsError, match="does not match"):
        install(lock, tmp_path, _mock_client(_archive({f"{PREFIX}/x": b"tampered"})))
    with pytest.raises(httpx.HTTPStatusError):
        download(lock, _mock_client(b"", 404))
    with pytest.raises(SkillsError, match="larger than expected"):
        download(lock, _mock_client(b"x" * (50 * 1024 * 1024 + 1)))


def _repo_copy(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / ".vscode").mkdir(parents=True)
    (root / ".claude").mkdir()
    shutil.copy(REPO_ROOT / ".gitignore", root / ".gitignore")
    shutil.copy(REPO_ROOT / ".vscode" / "settings.json", root / ".vscode" / "settings.json")
    shutil.copy(REPO_ROOT / ".claude" / "settings.json", root / ".claude" / "settings.json")
    return root


def test_check_requires_gitignore_and_approval_rules(tmp_path: Path) -> None:
    lock = load_lock(CONFIG_ROOT)
    root = _repo_copy(tmp_path)
    assert check(lock, root) == []
    (root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    settings = json.loads((root / ".vscode" / "settings.json").read_text(encoding="utf-8"))
    settings["chat.tools.terminal.autoApprove"][AZ_REST_RULE] = True
    (root / ".vscode" / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    (root / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    errors = check(lock, root)
    assert sum("must be listed in .gitignore" in e for e in errors) == 5
    assert any("require approval for `az rest`" in e for e in errors)
    assert any(".claude/settings.json must ask" in e for e in errors)


def test_skills_cli(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    assert main(["skills", "check"]) == 0
    assert "approval rules: OK" in capsys.readouterr().out

    data = _archive()
    config = tmp_path / "config"
    (config / "skills").mkdir(parents=True)
    lock = _lock(data)
    (config / "skills" / "fabric-skills.lock.yaml").write_text(
        json.dumps(lock.model_dump()), encoding="utf-8"
    )
    (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "settings.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("FFIA_CONFIG_ROOT", str(config))
    assert main(["skills", "status"]) == 1

    class FakeClient(httpx.Client):
        def __init__(self) -> None:
            super().__init__(
                transport=httpx.MockTransport(lambda _: httpx.Response(200, content=data))
            )

    monkeypatch.setattr(skills_commands.httpx, "Client", FakeClient)
    assert main(["skills", "install"]) == 0
    assert "was NOT installed" in capsys.readouterr().out
    assert main(["skills", "status"]) == 0
    assert "installed (v0.3.18)" in capsys.readouterr().out
    assert main(["skills", "check"]) == 1  # the temp repo has no .gitignore entries

    tampered = _lock(data, sha256="1" * 64)
    (config / "skills" / "fabric-skills.lock.yaml").write_text(
        json.dumps(tampered.model_dump()), encoding="utf-8"
    )
    assert main(["skills", "install"]) == 1
    assert "refusing to install" in capsys.readouterr().err
