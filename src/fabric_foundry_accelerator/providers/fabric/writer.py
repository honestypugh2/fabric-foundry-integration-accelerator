"""The scoped live writer: the only code path that changes a real Fabric workspace.

It runs only when every gate has passed:

- policy allowed the plan;
- a different person approved it;
- ``FFIA_ALLOW_LIVE_MUTATION=1`` and ``FFIA_FABRIC_LIVE=1`` are set;
- the target workspace alias is bound to an exact workspace ID in the git-ignored local bindings
  file.

It supports two narrow operations. Before writing, it re-checks for duplicates against the live
workspace. After writing, it verifies the item exists with the expected type and name. Notebooks
are created only from a reviewed definition committed under ``fabric/workspace/``.
"""

import base64
from pathlib import Path
from typing import Protocol

from fabric_foundry_accelerator.config.bindings import BindingsError, TenantBindings
from fabric_foundry_accelerator.models.changes import ProposedChange
from fabric_foundry_accelerator.models.checks import CheckResult
from fabric_foundry_accelerator.models.execution import EvidenceCategory
from fabric_foundry_accelerator.providers.fabric.rest import FabricRestClient

WRITER_NAME = "Fabric scoped writer (live)"
SUPPORTED: dict[str, tuple[str, str]] = {
    # operation: (item type, REST collection)
    "create_lakehouse": ("Lakehouse", "lakehouses"),
    "create_notebook": ("Notebook", "notebooks"),
}


class LiveWriter(Protocol):
    """A narrowly scoped writer for approved LIVE changes."""

    @property
    def name(self) -> str:
        """Writer name for envelopes and audit."""
        ...

    def supports(self, operation: str) -> bool:
        """Return True when the writer implements ``operation``."""
        ...

    async def precheck(self, plan: ProposedChange) -> CheckResult:
        """Re-check preconditions against the live workspace immediately before writing."""
        ...

    async def execute(self, plan: ProposedChange) -> str:
        """Perform exactly the approved change and return the created item ID."""
        ...

    async def verify(self, plan: ProposedChange, item_id: str) -> CheckResult:
        """Confirm the change against the live workspace."""
        ...


def notebook_definition_dir(definitions_root: Path, name: str) -> Path:
    """Return the Git-format folder that holds a reviewed notebook definition."""
    return definitions_root / f"{name}.Notebook"


class FabricScopedWriter:
    """Implements ``LiveWriter`` over the Fabric REST API for the bound workspaces only."""

    def __init__(
        self, client: FabricRestClient, bindings: TenantBindings, *, definitions_root: Path
    ) -> None:
        """Create a writer bound to the local tenant bindings."""
        self._client = client
        self._bindings = bindings
        self._definitions_root = definitions_root

    @property
    def name(self) -> str:
        """Writer name."""
        return WRITER_NAME

    def supports(self, operation: str) -> bool:
        """Only the operations in ``SUPPORTED``."""
        return operation in SUPPORTED

    def _workspace(self, plan: ProposedChange) -> str:
        workspace_id = self._bindings.workspace_id(plan.target.workspace_alias)
        if workspace_id is None:
            raise BindingsError(
                f"workspace alias {plan.target.workspace_alias!r} is not bound to a workspace ID "
                "in the local bindings file"
            )
        return workspace_id

    async def _matching(self, plan: ProposedChange) -> list[str]:
        item_type, _ = SUPPORTED[plan.operation]
        rows = await self._client.get_all(
            f"/workspaces/{self._workspace(plan)}/items", params={"type": item_type}
        )
        wanted = plan.target.item_name.casefold()
        return [str(r["id"]) for r in rows if str(r.get("displayName", "")).casefold() == wanted]

    async def precheck(self, plan: ProposedChange) -> CheckResult:
        """No item with the same type and name may already exist in the bound workspace."""
        existing = await self._matching(plan)
        return CheckResult(
            name="No duplicate item exists (live re-check)",
            passed=not existing,
            detail=(
                f"{plan.target.item_type} {plan.target.item_name!r} already exists in the bound workspace"
                if existing
                else f"{plan.target.item_type} {plan.target.item_name!r} not found in the bound workspace"
            ),
            category=EvidenceCategory.VERIFIED_LIVE,
        )

    def _notebook_parts(self, name: str) -> list[dict[str, str]]:
        folder = notebook_definition_dir(self._definitions_root, name)
        content = folder / "notebook-content.py"
        if not content.is_file():
            raise BindingsError(
                f"no reviewed notebook definition at {folder}; notebooks are created only from committed definitions"
            )
        parts = [content]
        platform = folder / ".platform"
        if platform.is_file():
            parts.append(platform)
        return [
            {
                "path": part.name,
                "payload": base64.b64encode(part.read_bytes()).decode("ascii"),
                "payloadType": "InlineBase64",
            }
            for part in parts
        ]

    async def execute(self, plan: ProposedChange) -> str:
        """Create the item; return its ID."""
        if not self.supports(plan.operation):
            raise BindingsError(
                f"operation {plan.operation!r} is not supported by the scoped writer"
            )
        _, collection = SUPPORTED[plan.operation]
        body: dict[str, object] = {
            "displayName": plan.target.item_name,
            "description": f"Created by the accelerator's scoped writer for approved change {plan.change_id}.",
        }
        if plan.operation == "create_notebook":
            body["definition"] = {
                "format": "fabricGitSource",
                "parts": self._notebook_parts(plan.target.item_name),
            }
        created = await self._client.post_fabric(
            f"/workspaces/{self._workspace(plan)}/{collection}", body
        )
        item_id = str(created.get("id", ""))
        if not item_id:
            matches = await self._matching(plan)
            item_id = matches[0] if matches else ""
        return item_id

    async def verify(self, plan: ProposedChange, item_id: str) -> CheckResult:
        """Exactly one item with the approved name and type, matching the returned ID."""
        matches = await self._matching(plan)
        passed = len(matches) == 1 and (not item_id or matches[0] == item_id)
        return CheckResult(
            name="Item exists exactly once with the approved name and type (live)",
            passed=passed,
            detail=f"{len(matches)} matching {plan.target.item_type} item(s) after the write",
            category=EvidenceCategory.VERIFIED_LIVE,
        )
