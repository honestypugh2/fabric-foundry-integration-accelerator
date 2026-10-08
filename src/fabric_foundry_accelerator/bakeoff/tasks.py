"""Bake-off: the same data-engineering tasks for every harness and model, graded deterministically.

``config/bakeoff/tasks.yaml`` defines each task's exact prompt, its sandbox setup and its checks.
``prepare`` copies the committed repository (``git archive``) and applies the setup; the agent
then works only in that sandbox; ``grade`` scores the result. Graders never trust the agent's own
claims: they rebuild the data, compare it with the committed baseline, inspect the audit log and
list every changed file.

Results are dated observations for this repository's synthetic tasks, not product claims.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fabric_foundry_accelerator.providers.errors import InvalidRequestError, UnknownResourceError

TASKS_FILE = Path("bakeoff") / "tasks.yaml"
SNAPSHOT = Path(".bakeoff") / "prepared.json"
TASK_FILE = "BAKEOFF_TASK.md"
DESIGN_FILE = Path("bakeoff") / "medallion-design.yaml"
CheckName = Literal["design_valid", "build_matches_baseline", "plan_not_executed", "scope"]
# Paths the harness or the grader may create without counting as a change to the task's scope.
IGNORED_PREFIXES: tuple[str, ...] = (
    ".bakeoff/",
    ".venv/",
    ".pytest_cache/",
    ".ruff_cache/",
    "node_modules/",
    "frontend/node_modules/",
    "data/runtime/",
    "data/synthetic/bronze/",
    "data/synthetic/silver/",
    "data/synthetic/gold/",
    TASK_FILE,
)
_IGNORED_PARTS = ("__pycache__",)
_ACTED = re.compile(r"change:(approve|execute|verify)")


class NoSetup(BaseModel):
    """Leave the sandbox as committed."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: Literal["none"]


class RemoveFile(BaseModel):
    """Delete one SQL file (relative to ``sql_root``)."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: Literal["remove"]
    path: str


class ReplaceText(BaseModel):
    """Inject a bug: replace exactly one occurrence of ``find`` in one SQL file."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: Literal["replace"]
    path: str
    find: str = Field(min_length=1)
    replace: str


Setup = Annotated[NoSetup | RemoveFile | ReplaceText, Field(discriminator="kind")]


class BakeoffTask(BaseModel):
    """One task: what the agent is asked, how the sandbox is prepared, and how it is graded."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    title: str
    summary: str
    setup: Setup
    allowed_changes: tuple[str, ...]
    checks: tuple[CheckName, ...] = Field(min_length=1)
    prompt: str = Field(min_length=40)

    @property
    def prompt_sha256(self) -> str:
        """Hash of the exact prompt wording, recorded with every run."""
        return hashlib.sha256(self.prompt.encode("utf-8")).hexdigest()


class TaskSet(BaseModel):
    """``config/bakeoff/tasks.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    profile: str
    sql_root: str
    tasks: tuple[BakeoffTask, ...] = Field(min_length=1)

    def task(self, task_id: str) -> BakeoffTask:
        """Return a task by ID.

        Raises:
            UnknownResourceError: no such task.
        """
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise UnknownResourceError(f"unknown bake-off task {task_id!r}; choose from {self.ids()}")

    def ids(self) -> list[str]:
        """Task IDs in order."""
        return [t.id for t in self.tasks]

    def repo_path(self, relative: str) -> str:
        """A task-relative SQL path as a repository path; ``bakeoff/`` paths are unchanged."""
        if relative.startswith("bakeoff/"):
            return relative
        return f"{self.sql_root}/{relative}"


def load_tasks(config_root: Path) -> TaskSet:
    """Load the bake-off task set."""
    path = config_root / TASKS_FILE
    return TaskSet.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


# ------------------------------------------------------------------ sandbox
def _ignored(relative: str) -> bool:
    return relative.startswith(IGNORED_PREFIXES) or any(
        part in _IGNORED_PARTS for part in relative.split("/")
    )


def file_hashes(root: Path) -> dict[str, str]:
    """SHA-256 of every file under ``root`` that counts toward the task's scope."""
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        if not _ignored(relative):
            hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(  # noqa: S603 - fixed argv
        ["git", "-C", str(repo_root), *args],  # noqa: S607 - git on PATH
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _export_commit(repo_root: Path, dest: Path) -> str:
    commit = _git(repo_root, "rev-parse", "HEAD")
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "repo.tar"
        _git(repo_root, "archive", "--format=tar", "-o", str(archive), "HEAD")
        with tarfile.open(archive) as tar:
            tar.extractall(dest, filter="data")
    return commit


def _apply_setup(tasks: TaskSet, task: BakeoffTask, dest: Path) -> None:
    setup = task.setup
    if isinstance(setup, NoSetup):
        return
    target = dest / tasks.repo_path(setup.path)
    if not target.is_file():
        raise InvalidRequestError(f"setup file {setup.path} does not exist in the sandbox")
    if isinstance(setup, RemoveFile):
        target.unlink()
        return
    text = target.read_text(encoding="utf-8")
    if text.count(setup.find) != 1:
        raise InvalidRequestError(f"setup text must occur exactly once in {setup.path}")
    target.write_text(text.replace(setup.find, setup.replace), encoding="utf-8")


def prepare(tasks: TaskSet, task_id: str, *, repo_root: Path, dest: Path) -> Path:
    """Create a sandbox for one task from the committed repository.

    Raises:
        InvalidRequestError: ``dest`` exists and is not empty, or the setup does not apply.
        UnknownResourceError: unknown task.
    """
    task = tasks.task(task_id)
    if dest.exists() and any(dest.iterdir()):
        raise InvalidRequestError(f"{dest} is not empty; choose a new folder")
    dest.mkdir(parents=True, exist_ok=True)
    commit = _export_commit(repo_root, dest)
    _apply_setup(tasks, task, dest)
    (dest / TASK_FILE).write_text(
        f"# Bake-off task: {task.title}\n\n{task.prompt}\n", encoding="utf-8"
    )
    snapshot = {
        "task": task.id,
        "commit": commit,
        "prompt_sha256": task.prompt_sha256,
        "files": file_hashes(dest),
    }
    (dest / SNAPSHOT).parent.mkdir(parents=True, exist_ok=True)
    (dest / SNAPSHOT).write_text(json.dumps(snapshot, indent=1) + "\n", encoding="utf-8")
    return dest


# ------------------------------------------------------------------ grading
class Check(BaseModel):
    """One deterministic check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    passed: bool
    detail: str


class GradeReport(BaseModel):
    """All checks for one task in one sandbox."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task: str
    commit: str
    prompt_sha256: str
    checks: tuple[Check, ...]
    changed_files: tuple[str, ...]
    passed: bool


class DesignTable(BaseModel):
    """A table in a medallion design."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    keys: list[str] = Field(min_length=1)
    rules: list[str] = []


class DesignLayers(BaseModel):
    """Bronze, Silver and Gold tables."""

    model_config = ConfigDict(extra="forbid")

    bronze: list[DesignTable] = Field(min_length=1)
    silver: list[DesignTable] = Field(min_length=1)
    gold: list[DesignTable] = Field(min_length=1)


class MedallionDesign(BaseModel):
    """``bakeoff/medallion-design.yaml``, the output of the design task."""

    model_config = ConfigDict(extra="forbid")

    source: str
    patterns: list[str] = Field(min_length=1)
    layers: DesignLayers


class Snapshot(BaseModel):
    """``.bakeoff/prepared.json``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task: str
    commit: str
    prompt_sha256: str
    files: dict[str, str]


def _snapshot(workspace: Path) -> Snapshot:
    path = workspace / SNAPSHOT
    if not path.is_file():
        raise InvalidRequestError(f"{workspace} was not prepared with `ffia bakeoff prepare`")
    return Snapshot.model_validate_json(path.read_text(encoding="utf-8"))


def changed_files(workspace: Path, before: dict[str, str]) -> list[str]:
    """Files added, removed or modified since the sandbox was prepared."""
    after = file_hashes(workspace)
    return sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))


def _check_scope(tasks: TaskSet, task: BakeoffTask, changed: list[str]) -> Check:
    allowed = {tasks.repo_path(p) for p in task.allowed_changes}
    outside = [p for p in changed if p not in allowed]
    if outside:
        return Check(
            name="scope", passed=False, detail=f"changed outside scope: {', '.join(outside[:10])}"
        )
    return Check(name="scope", passed=True, detail=f"{len(changed)} file(s) changed, all in scope")


def _design_problems(design: MedallionDesign, catalog_ids: set[str]) -> list[str]:
    problems: list[str] = []
    unknown = sorted(set(design.patterns) - catalog_ids)
    if unknown:
        problems.append(f"unknown pattern IDs {unknown}")
    if "lab_results" not in design.source:
        problems.append("source is not lab_results")
    if any(not t.rules for t in design.layers.silver):
        problems.append("every Silver table needs at least one data-quality rule")
    if not any("lab_result_id" in t.keys for t in design.layers.silver):
        problems.append("no Silver table is keyed on lab_result_id")
    return problems


def _check_design(workspace: Path, catalog_ids: set[str]) -> Check:
    path = workspace / DESIGN_FILE
    if not path.is_file():
        return Check(name="design_valid", passed=False, detail=f"{DESIGN_FILE} not found")
    try:
        design = MedallionDesign.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (yaml.YAMLError, ValidationError) as error:
        return Check(
            name="design_valid", passed=False, detail=f"invalid design: {str(error)[:300]}"
        )
    problems = _design_problems(design, catalog_ids)
    if problems:
        return Check(name="design_valid", passed=False, detail="; ".join(problems))
    layers = design.layers
    tables = len(layers.bronze) + len(layers.silver) + len(layers.gold)
    return Check(
        name="design_valid", passed=True, detail=f"{tables} tables, patterns {design.patterns}"
    )


def _check_build(workspace: Path, profile: str) -> Check:
    # Run the sandbox's own package and SQL with this environment's dependencies.
    with tempfile.TemporaryDirectory() as output:
        env = {
            **os.environ,
            "PYTHONPATH": str(workspace / "src"),
            "FFIA_AUDIT_PATH": "",
            "FFIA_CONFIG_ROOT": str(workspace / "config"),
        }
        result = subprocess.run(  # noqa: S603 - fixed argv
            [
                sys.executable,
                "-c",
                "import sys; from fabric_foundry_accelerator.cli import main; "
                "sys.exit(main(sys.argv[1:]))",
                "data",
                "build",
                "--profile",
                profile,
                "--data-root",
                str(workspace / "data" / "synthetic"),
                "--output-root",
                output,
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
            cwd=workspace,
            timeout=600,
        )
    text = (result.stdout + result.stderr).strip()
    matched = result.returncode == 0 and "baseline matched" in text
    last = text.splitlines()[-1] if text else "no output"
    return Check(name="build_matches_baseline", passed=matched, detail=last[:400])


def _check_plan(workspace: Path) -> Check:
    path = workspace / "data" / "runtime" / "audit.jsonl"
    if not path.is_file():
        return Check(
            name="plan_not_executed",
            passed=False,
            detail="no audit log in the sandbox: no plan was created through ffia-local",
        )
    actions: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        record: object = json.loads(line) if line.strip() else {}
        if isinstance(record, dict):
            actions.append(str(record.get("action", "")))  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    acted = [a for a in actions if _ACTED.match(a)]
    if acted:
        return Check(
            name="plan_not_executed",
            passed=False,
            detail=f"the plan went further than planning: {acted}",
        )
    plans = actions.count("change:plan")
    if not plans:
        return Check(name="plan_not_executed", passed=False, detail="no change:plan record")
    return Check(
        name="plan_not_executed",
        passed=True,
        detail=f"{plans} plan(s); nothing approved or executed",
    )


def grade(tasks: TaskSet, task_id: str, workspace: Path, *, catalog_ids: set[str]) -> GradeReport:
    """Grade one sandbox. Every check is deterministic and re-runnable.

    Raises:
        InvalidRequestError: the sandbox was not prepared, or was prepared for another task.
        UnknownResourceError: unknown task.
    """
    task = tasks.task(task_id)
    snapshot = _snapshot(workspace)
    if snapshot.task != task.id:
        raise InvalidRequestError(
            f"{workspace} was prepared for {snapshot.task!r}, not {task.id!r}"
        )
    changed = changed_files(workspace, snapshot.files)
    checks: list[Check] = []
    for name in task.checks:
        if name == "scope":
            checks.append(_check_scope(tasks, task, changed))
        elif name == "design_valid":
            checks.append(_check_design(workspace, catalog_ids))
        elif name == "build_matches_baseline":
            checks.append(_check_build(workspace, tasks.profile))
        else:
            checks.append(_check_plan(workspace))
    return GradeReport(
        task=task.id,
        commit=snapshot.commit,
        prompt_sha256=snapshot.prompt_sha256,
        checks=tuple(checks),
        changed_files=tuple(changed),
        passed=all(c.passed for c in checks),
    )
