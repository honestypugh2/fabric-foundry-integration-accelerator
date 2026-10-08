"""Repository leak scanner.

Detects content that must never enter the repository:

* customer-identifying terms, matched through a **salted, hashed denylist** so the
  repository never stores the plaintext terms it is protecting;
* GUIDs (tenant, workspace, item and capacity identifiers);
* secret-like material (keys, tokens, connection strings);
* e-mail addresses outside documentation-reserved domains.

The hashed denylist is an obfuscation control, not cryptographic secrecy: short
terms can be guessed by dictionary attack. Plaintext terms may additionally be
supplied from an untracked local file or a CI secret (``FFIA_LEAK_DENYLIST``).
"""

import hashlib
import os
import re
import shutil
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

ALLOW_MARKER = "leak-scan: allow"
"""Inline marker that suppresses findings on a single line. Use with a justification."""

DENYLIST_ENV_VAR = "FFIA_LEAK_DENYLIST"
LOCAL_DENYLIST_PATH = Path(".privacy/denylist.local.txt")
DEFAULT_DENYLIST_PATH = Path("config/privacy/denylist.yaml")
MAX_NGRAM = 3
MAX_FILE_BYTES = 2_000_000

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_HEX64_RE = r"^[0-9a-f]{64}$"

GUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
ALLOWED_GUIDS = frozenset({"00000000-0000-0000-0000-000000000000"})
# Synthetic fixture identifiers: the first four groups are zero. Real tenant, workspace and item
# IDs are random v4 GUIDs and never have this shape.
SYNTHETIC_GUID_PREFIX = "00000000-0000-0000-0000-"

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})\b")
ALLOWED_EMAIL_DOMAINS = frozenset(
    {"example.com", "example.org", "example.net", "users.noreply.github.com"}
)

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "JSON web token",
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}")),
    ("Azure storage account key", re.compile(r"AccountKey=[A-Za-z0-9+/=]{20,}")),
    ("Azure SAS signature", re.compile(r"[?&]sig=[A-Za-z0-9%]{20,}")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI-style API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    (
        "assigned secret literal",
        re.compile(
            r"(?i)\b(?:password|passwd|secret|api[_-]?key|client[_-]?secret|access[_-]?token)\b"
            r"\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"
        ),
    ),
)

_SKIP_DIRS = frozenset(
    {".git", ".venv", "node_modules", "dist", "build", ".pytest_cache", ".ruff_cache", "coverage"}
)


class FindingKind(StrEnum):
    """Category of a leak-scan finding."""

    DENYLIST = "denylist"
    GUID = "guid"
    SECRET = "secret"  # noqa: S105 - category label, not a credential
    EMAIL = "email"


@dataclass(frozen=True, slots=True)
class Finding:
    """A single finding. ``detail`` never contains the matched sensitive value."""

    path: str
    line: int
    kind: FindingKind
    detail: str

    def render(self) -> str:
        """Return a single-line, redacted, human-readable description."""
        return f"{self.path}:{self.line}: [{self.kind}] {self.detail}"


class DenylistFile(BaseModel):
    """On-disk format of the committed, hashed denylist."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1] = 1
    salt: str = Field(min_length=16)
    hashes: list[str] = Field(default_factory=list[str])

    def validated_hashes(self) -> frozenset[str]:
        """Return hashes after format validation."""
        pattern = re.compile(_HEX64_RE)
        bad = [h for h in self.hashes if not pattern.match(h)]
        if bad:
            raise ValueError(f"denylist contains {len(bad)} malformed hash entries")
        return frozenset(self.hashes)


def normalize_term(term: str) -> str:
    """Normalize a term to lowercase alphanumeric tokens joined by single spaces."""
    return " ".join(_TOKEN_RE.findall(term.lower()))


def hash_term(term: str, salt: str) -> str:
    """Return the salted SHA-256 hex digest of a normalized term."""
    normalized = normalize_term(term)
    return hashlib.sha256(f"{salt}\x00{normalized}".encode()).hexdigest()


def normalize_ngrams(text: str, max_n: int = MAX_NGRAM) -> set[str]:
    """Return all 1..max_n token n-grams of ``text`` after normalization."""
    tokens = _TOKEN_RE.findall(text.lower())
    grams: set[str] = set()
    for size in range(1, max_n + 1):
        for start in range(len(tokens) - size + 1):
            grams.add(" ".join(tokens[start : start + size]))
    return grams


class Denylist:
    """A set of salted term hashes used to detect customer-identifying text."""

    def __init__(self, salt: str, hashes: Iterable[str] = (), terms: Iterable[str] = ()) -> None:
        """Create a denylist from existing hashes and optional plaintext terms."""
        self._salt = salt
        extra = {hash_term(t, salt) for t in terms if normalize_term(t)}
        self._hashes = frozenset(hashes) | frozenset(extra)

    @property
    def salt(self) -> str:
        """Return the salt used for hashing."""
        return self._salt

    @property
    def hashes(self) -> frozenset[str]:
        """Return all term hashes."""
        return self._hashes

    def __len__(self) -> int:
        """Return the number of hashed terms."""
        return len(self._hashes)

    def matches(self, text: str) -> bool:
        """Return True when any 1..3-token n-gram of ``text`` is denylisted."""
        if not self._hashes:
            return False
        return any(hash_term(gram, self._salt) in self._hashes for gram in normalize_ngrams(text))

    @classmethod
    def load(
        cls,
        path: Path,
        *,
        local_terms_path: Path | None = None,
        environ: dict[str, str] | None = None,
    ) -> Denylist:
        """Load the committed hashed denylist plus optional local and CI plaintext terms."""
        data = DenylistFile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        terms: list[str] = []
        if local_terms_path is not None and local_terms_path.is_file():
            terms.extend(_read_terms(local_terms_path.read_text(encoding="utf-8")))
        env = os.environ if environ is None else environ
        terms.extend(_read_terms(env.get(DENYLIST_ENV_VAR, "")))
        return cls(data.salt, data.validated_hashes(), terms)


def _read_terms(raw: str) -> list[str]:
    return [line.strip() for line in raw.splitlines() if line.strip() and not line.startswith("#")]


def add_terms_to_file(path: Path, terms: Sequence[str]) -> int:
    """Hash ``terms`` into the denylist file at ``path``; return the number of new hashes.

    Terms longer than three tokens are rejected because the scanner matches n-grams
    of up to three tokens.
    """
    data = DenylistFile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    existing = set(data.validated_hashes())
    added = 0
    for term in terms:
        normalized = normalize_term(term)
        if not normalized:
            continue
        if len(normalized.split(" ")) > MAX_NGRAM:
            raise ValueError(f"terms may contain at most {MAX_NGRAM} tokens")
        digest = hash_term(normalized, data.salt)
        if digest not in existing:
            existing.add(digest)
            added += 1
    updated = DenylistFile(version=1, salt=data.salt, hashes=sorted(existing))
    path.write_text(
        "# Salted SHA-256 hashes of customer-identifying terms. Never add plaintext here.\n"
        "# Manage with: uv run ffia privacy add-terms (reads terms from stdin).\n"
        + yaml.safe_dump(updated.model_dump(), sort_keys=False),
        encoding="utf-8",
    )
    return added


def scan_text(text: str, *, path: str, denylist: Denylist | None = None) -> list[Finding]:
    """Scan text and return redacted findings."""
    findings: list[Finding] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in line:
            continue
        findings.extend(_scan_line(line, path=path, number=number, denylist=denylist))
    return findings


def _scan_line(line: str, *, path: str, number: int, denylist: Denylist | None) -> list[Finding]:
    found: list[Finding] = []
    if denylist is not None and denylist.matches(line):
        found.append(
            Finding(path, number, FindingKind.DENYLIST, "customer-identifying term (hashed match)")
        )
    found.extend(
        Finding(path, number, FindingKind.GUID, "GUID-formatted identifier")
        for match in GUID_RE.finditer(line)
        if match.group(0).lower() not in ALLOWED_GUIDS
        and not match.group(0).lower().startswith(SYNTHETIC_GUID_PREFIX)
    )
    found.extend(
        Finding(path, number, FindingKind.SECRET, f"possible {label}")
        for label, pattern in SECRET_PATTERNS
        if pattern.search(line)
    )
    found.extend(
        Finding(path, number, FindingKind.EMAIL, "e-mail address outside reserved domains")
        for match in EMAIL_RE.finditer(line)
        if match.group(1).lower() not in ALLOWED_EMAIL_DOMAINS
    )
    return found


def _is_scannable(path: Path, excluded: frozenset[Path]) -> bool:
    if not path.is_file() or path.resolve() in excluded:
        return False
    if path.stat().st_size > MAX_FILE_BYTES:
        return False
    with path.open("rb") as handle:
        return b"\0" not in handle.read(8192)


def scan_paths(
    paths: Iterable[Path],
    *,
    root: Path,
    denylist: Denylist | None = None,
    exclude: Iterable[Path] = (),
) -> list[Finding]:
    """Scan files and return redacted findings with paths relative to ``root``."""
    excluded = frozenset(p.resolve() for p in exclude)
    findings: list[Finding] = []
    for path in paths:
        if not _is_scannable(path, excluded):
            continue
        try:
            display = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            display = path.as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        findings.extend(scan_text(text, path=display, denylist=denylist))
    return findings


def list_repository_files(root: Path) -> list[Path]:
    """List tracked and untracked-but-not-ignored files; fall back to a directory walk."""
    git = shutil.which("git")
    if git is not None and (root / ".git").exists():
        # Fixed argument list, no shell, executable resolved from PATH: safe subprocess use.
        result = subprocess.run(  # noqa: S603
            [git, "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            check=True,
            capture_output=True,
        )
        names = [n for n in result.stdout.decode("utf-8").split("\0") if n]
        return [root / name for name in names]
    return [
        p
        for p in root.rglob("*")
        if p.is_file() and not any(part in _SKIP_DIRS for part in p.relative_to(root).parts)
    ]
