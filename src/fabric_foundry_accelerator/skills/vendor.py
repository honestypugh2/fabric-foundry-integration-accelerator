"""Install pinned third-party agent skills safely.

The lock file names one release archive, its SHA-256 and a curated subset of skills. Installation
downloads that archive, refuses any hash mismatch, and extracts only the allow-listed folders into
git-ignored paths. Nothing else from the archive (agent personas, MCP configuration) is written.
"""

import hashlib
import io
import json
import shutil
import tarfile
from pathlib import Path, PurePosixPath

import httpx
import yaml
from pydantic import BaseModel, ConfigDict, Field

LOCK_FILE = Path("skills") / "fabric-skills.lock.yaml"
PIN_FILE = ".ffia-pin"
_NAME = r"^[a-z0-9]+(-[a-z0-9]+)*$"
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
# Skills call Fabric with `az rest` outside MCP, so every such command needs a person to approve it.
AZ_REST_RULE = r"/^az\s+rest\b/"


class SkillsError(ValueError):
    """Raised when the lock file, archive or installation is invalid."""


class VendoredSkill(BaseModel):
    """One allow-listed skill."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(pattern=_NAME)
    why: str


class SkillsLock(BaseModel):
    """``config/skills/fabric-skills.lock.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source: str
    license: str
    tag: str = Field(pattern=r"^v\d+\.\d+\.\d+$")
    published: str
    archive_url: str = Field(pattern=r"^https://codeload\.github\.com/")
    archive_prefix: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    install_root: str
    skills: tuple[VendoredSkill, ...] = Field(min_length=1)
    support_dirs: tuple[str, ...] = ()

    def allowed_prefixes(self) -> dict[str, str]:
        """Map archive folders to install folders (both relative)."""
        mapping = {f"skills/{s.name}": f"skills/{s.name}" for s in self.skills}
        mapping.update({d: d for d in self.support_dirs})
        return mapping

    def install_dirs(self, repo_root: Path) -> list[Path]:
        """Every folder the install writes."""
        root = repo_root / self.install_root
        return [root / target for target in self.allowed_prefixes().values()]


def load_lock(config_root: Path) -> SkillsLock:
    """Load the skills lock file."""
    data = yaml.safe_load((config_root / LOCK_FILE).read_text(encoding="utf-8"))
    return SkillsLock.model_validate(data)


def verify_archive(lock: SkillsLock, data: bytes) -> None:
    """Refuse an archive whose SHA-256 differs from the lock."""
    digest = hashlib.sha256(data).hexdigest()
    if digest != lock.sha256:
        raise SkillsError(
            f"archive hash {digest} does not match the pinned {lock.sha256}; refusing to install"
        )


def _target(lock: SkillsLock, member: str) -> PurePosixPath | None:
    path = PurePosixPath(member)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise SkillsError(f"unsafe path in archive: {member}")
    if path.parts[0] != lock.archive_prefix:
        return None
    inner = PurePosixPath(*path.parts[1:])
    for source, target in lock.allowed_prefixes().items():
        prefix = PurePosixPath(source)
        if inner == prefix or prefix in inner.parents:
            return PurePosixPath(target) / inner.relative_to(prefix)
    return None


def extract(lock: SkillsLock, data: bytes, repo_root: Path) -> list[Path]:
    """Extract only allow-listed regular files; return the written files."""
    root = repo_root / lock.install_root
    for folder in lock.install_dirs(repo_root):
        if folder.exists():
            shutil.rmtree(folder)
    written: list[Path] = []
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive.getmembers():
            target = _target(lock, member.name)
            if target is None or not member.isfile():
                continue  # directories are implied; links and devices are never written
            source = archive.extractfile(member)
            if source is None:  # pragma: no cover - regular files always have content
                continue
            destination = root / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read())
            written.append(destination)
    for skill in lock.skills:
        folder = root / "skills" / skill.name
        if not (folder / "SKILL.md").is_file():
            raise SkillsError(f"skill {skill.name!r} is not in {lock.source}@{lock.tag}")
        (folder / PIN_FILE).write_text(
            f"{lock.source}@{lock.tag} sha256:{lock.sha256}\n", encoding="utf-8"
        )
    return written


def download(lock: SkillsLock, client: httpx.Client) -> bytes:
    """Download the pinned archive (bounded size)."""
    response = client.get(lock.archive_url, follow_redirects=True, timeout=60.0)
    response.raise_for_status()
    if len(response.content) > MAX_ARCHIVE_BYTES:
        raise SkillsError("archive is larger than expected; refusing to install")
    return response.content


def install(lock: SkillsLock, repo_root: Path, client: httpx.Client) -> list[Path]:
    """Download, verify and extract the curated skills."""
    data = download(lock, client)
    verify_archive(lock, data)
    return extract(lock, data, repo_root)


def status(lock: SkillsLock, repo_root: Path) -> dict[str, str]:
    """Return each skill's state: installed (pinned), stale pin, or missing."""
    expected = f"{lock.source}@{lock.tag} sha256:{lock.sha256}"
    result: dict[str, str] = {}
    for skill in lock.skills:
        pin = repo_root / lock.install_root / "skills" / skill.name / PIN_FILE
        if not pin.is_file():
            result[skill.name] = "missing"
        elif pin.read_text(encoding="utf-8").strip() == expected:
            result[skill.name] = f"installed ({lock.tag})"
        else:
            result[skill.name] = "stale pin"
    return result


def check(lock: SkillsLock, repo_root: Path) -> list[str]:
    """Offline checks: every install folder is git-ignored and approval rules are committed."""
    errors: list[str] = []
    ignore = (repo_root / ".gitignore").read_text(encoding="utf-8").splitlines()
    for folder in lock.install_dirs(repo_root):
        relative = folder.relative_to(repo_root).as_posix() + "/"
        if relative not in ignore:
            errors.append(
                f"{relative} must be listed in .gitignore (vendored content is never committed)"
            )
    vscode = json.loads((repo_root / ".vscode" / "settings.json").read_text(encoding="utf-8"))
    rules = vscode.get("chat.tools.terminal.autoApprove", {})
    if not isinstance(rules, dict) or rules.get(AZ_REST_RULE) is not False:  # pyright: ignore[reportUnknownMemberType]
        errors.append(
            ".vscode/settings.json must require approval for `az rest` "
            f'(chat.tools.terminal.autoApprove: "{AZ_REST_RULE}": false)'
        )
    claude = repo_root / ".claude" / "settings.json"
    if not claude.is_file() or "Bash(az rest:*)" not in claude.read_text(encoding="utf-8"):
        errors.append(".claude/settings.json must ask before `az rest` (permissions.ask)")
    return errors
