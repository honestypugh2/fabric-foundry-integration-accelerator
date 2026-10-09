"""Validate release SBOMs with the existing CycloneDX development toolchain."""

import re
import sys
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from cyclonedx.schema import SchemaVersion
from cyclonedx.validation.json import JsonStrictValidator
from pydantic import BaseModel, ConfigDict, Field

_GITHUB_SSH_PREFIX = "ssh://git@github.com/"  # leak-scan: allow - public Git SSH URI


class ExternalReference(BaseModel):
    """A reference with all exporter metadata preserved."""

    model_config = ConfigDict(extra="allow")

    type: str
    url: str


class Component(BaseModel):
    """Dependency identity needed for pin verification."""

    model_config = ConfigDict(extra="allow")

    name: str
    version: str
    external_references: tuple[ExternalReference, ...] = Field(
        default=(), alias="externalReferences"
    )


class Bom(BaseModel):
    """The subset of a CycloneDX boundary used after full schema validation."""

    model_config = ConfigDict(extra="allow")

    bom_format: Literal["CycloneDX"] = Field(alias="bomFormat")
    spec_version: str = Field(alias="specVersion", pattern=r"^1\.[0-7]$")
    components: tuple[Component, ...] = Field(min_length=1)


class PythonProject(BaseModel):
    """Runtime dependency pins from the Python manifest."""

    dependencies: tuple[str, ...]


class FrontendManifest(BaseModel):
    """Runtime dependency pins from the frontend manifest."""

    dependencies: dict[str, str]


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.lower())


def normalize_npm_vcs_references(path: Path) -> int:
    """Convert npm's GitHub SCP-style VCS references into schema-valid SSH URIs."""
    bom = Bom.model_validate_json(path.read_text(encoding="utf-8"))
    components: list[Component] = []
    count = 0
    for component in bom.components:
        references: list[ExternalReference] = []
        for reference in component.external_references:
            match = re.fullmatch(r"git@github\.com:([\w./-]+)", reference.url)
            if reference.type == "vcs" and match:
                references.append(
                    reference.model_copy(update={"url": f"{_GITHUB_SSH_PREFIX}{match.group(1)}"})
                )
                count += 1
            else:
                references.append(reference)
        components.append(
            component.model_copy(update={"external_references": tuple(references)})
            if component.external_references
            else component
        )
    if count:
        updated = bom.model_copy(update={"components": tuple(components)})
        path.write_text(
            updated.model_dump_json(by_alias=True, exclude_unset=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return count


def verify_sbom(path: Path, required: Mapping[str, str]) -> int:
    """Reject invalid schemas, missing runtime packages and incorrect exact pins."""
    text = path.read_text(encoding="utf-8")
    bom = Bom.model_validate_json(text)
    schema = SchemaVersion[f"V{bom.spec_version.replace('.', '_')}"]
    if JsonStrictValidator(schema).validate_str(text) is not None:
        raise ValueError(f"{path}: invalid CycloneDX schema")
    components = {(_normalize(c.name), c.version) for c in bom.components}
    missing = [
        f"{name}=={pin}"
        for name, pin in required.items()
        if (_normalize(name), pin) not in components
    ]
    if missing:
        raise ValueError(f"{path}: missing exact runtime pins: {', '.join(missing)}")
    return len(bom.components)


def main() -> None:
    """Check both installed-environment SBOMs against their runtime manifests."""
    with Path("pyproject.toml").open("rb") as stream:
        project = PythonProject.model_validate(tomllib.load(stream)["project"])
    python_pins: dict[str, str] = {}
    for requirement in project.dependencies:
        package, separator, pin = requirement.split(";", 1)[0].partition("==")
        if not separator:
            raise ValueError(f"runtime dependency is not exactly pinned: {package}")
        python_pins[package.split("[", 1)[0].strip()] = pin.strip()
    frontend = FrontendManifest.model_validate_json(
        Path("frontend/package.json").read_text(encoding="utf-8")
    )
    normalized = normalize_npm_vcs_references(Path("sbom/frontend.cdx.json"))
    if normalized:
        sys.stdout.write(f"LOCAL normalized {normalized} npm VCS references to SSH URIs\n")
    for name, pins in (("python", python_pins), ("frontend", frontend.dependencies)):
        path = Path("sbom") / f"{name}.cdx.json"
        count = verify_sbom(path, pins)
        sys.stdout.write(f"LOCAL {path}: schema valid, {count} components, runtime pins matched\n")


if __name__ == "__main__":
    main()
