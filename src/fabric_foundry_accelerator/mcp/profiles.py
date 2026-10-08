"""MCP profiles as code: typed loading, per-client rendering and safety checks.

``config/mcp/profiles.yaml`` is the single source for MCP client configuration. A profile names
the narrowest servers and tools for one job. ``check_profiles`` enforces the repository rules:

- external servers are pinned to exact stable versions;
- read-only profiles start servers with ``--read-only`` and an explicit allow-list;
- tools that run arbitrary queries or copy data out never appear in a read-only profile;
- every write-capable profile is opt-in and requires per-call human approval;
- the committed project ``.mcp.json`` is exactly the rendered default profile.
"""

import json
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.models.execution import ExecutionLabel

McpClient = Literal["vscode", "claude", "copilot-cli"]
CLIENTS: tuple[McpClient, ...] = ("vscode", "claude", "copilot-cli")
CLIENT_FILES: dict[McpClient, str] = {
    "vscode": ".vscode/mcp.json (workspace) or the user MCP configuration",
    "claude": ".mcp.json (project) for Claude Code",
    "copilot-cli": "~/.copilot/mcp-config.json for GitHub Copilot CLI",
}
EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
FORBIDDEN_ARGS = ("--dangerously", "--accept-eula", "--accepteula", "@latest")
PROJECT_MCP_FILE = ".mcp.json"


class ServerSpec(BaseModel):
    """One MCP server and how to start it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    transport: Literal["stdio", "http"]
    description: str
    url: str | None = None
    command: str | None = None
    package: str | None = None
    version: str | None = None
    args: tuple[str, ...] = ()
    catalog: str | None = None


class ProfileServer(BaseModel):
    """How a profile uses one server."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    read_only: bool | None = None
    tools: tuple[str, ...] = ()


class Profile(BaseModel):
    """A named, purpose-scoped set of servers and tools."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str
    purpose: str
    execution_label: ExecutionLabel
    default: bool = False
    approval: Literal["none", "per-call"] = "none"
    requires: tuple[str, ...] = ()
    servers: dict[str, ProfileServer]

    @property
    def writes(self) -> bool:
        """True when any server in the profile can write."""
        return any(s.read_only is False for s in self.servers.values())


class Exclusion(BaseModel):
    """A tool that is never allowed in a read-only profile."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    reason: str


class McpProfiles(BaseModel):
    """``config/mcp/profiles.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    servers: dict[str, ServerSpec]
    never_read_only: tuple[Exclusion, ...] = ()
    profiles: dict[str, Profile]

    def default_profile(self) -> str:
        """Return the name of the default profile."""
        defaults = [name for name, p in self.profiles.items() if p.default]
        if len(defaults) != 1:
            raise ValueError(f"exactly one default profile is required, found {defaults}")
        return defaults[0]


class CatalogTool(BaseModel):
    """One tool in a pinned server's catalog."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    read_only: bool
    destructive: bool


class ToolCatalog(BaseModel):
    """Tools exposed by one pinned server version, captured with the server's own discovery."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    package: str
    version: str
    captured_with: str
    captured_on: str
    tools: tuple[CatalogTool, ...] = Field(min_length=1)

    def get(self, name: str) -> CatalogTool | None:
        """Return a tool by name."""
        return next((t for t in self.tools if t.name == name), None)


def mcp_root(config_root: Path) -> Path:
    """Return the MCP configuration folder."""
    return config_root / "mcp"


def load_profiles(config_root: Path) -> McpProfiles:
    """Load and validate the profiles file."""
    path = mcp_root(config_root) / "profiles.yaml"
    return McpProfiles.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_tool_catalog(config_root: Path, relative: str) -> ToolCatalog:
    """Load a pinned tool catalog."""
    path = mcp_root(config_root) / relative
    return ToolCatalog.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def launch_args(spec: ServerSpec, usage: ProfileServer) -> tuple[str, list[str]]:
    """Return the command and arguments that start ``spec`` the way ``usage`` requires."""
    if spec.package:
        args = ["-y", f"{spec.package}@{spec.version}", *spec.args]
        if usage.read_only:
            args.append("--read-only")
        for tool in usage.tools:
            args += ["--tool", tool]
        return "npx", args
    return spec.command or "", list(spec.args)


def _entry(spec: ServerSpec, usage: ProfileServer, client: McpClient) -> dict[str, object]:
    if spec.transport == "http":
        entry: dict[str, object] = {"type": "http", "url": spec.url}
    else:
        command, args = launch_args(spec, usage)
        entry = {
            "type": "local" if client == "copilot-cli" else "stdio",
            "command": command,
            "args": args,
        }
    if client == "copilot-cli":
        # The server-side allow-list already narrows tools; Copilot CLI requires this key.
        entry["tools"] = ["*"]
    return entry


def render(profiles: McpProfiles, name: str, client: McpClient) -> dict[str, object]:
    """Render one profile as the JSON a client reads."""
    profile = profiles.profiles.get(name)
    if profile is None:
        raise KeyError(f"unknown MCP profile {name!r}; choose from {sorted(profiles.profiles)}")
    entries = {
        server: _entry(profiles.servers[server], usage, client)
        for server, usage in profile.servers.items()
    }
    root = "servers" if client == "vscode" else "mcpServers"
    return {root: entries}


def render_text(profiles: McpProfiles, name: str, client: McpClient) -> str:
    """Render one profile as formatted JSON text."""
    return json.dumps(render(profiles, name, client), indent=2) + "\n"


def _check_server(name: str, spec: ServerSpec) -> list[str]:
    errors: list[str] = []
    if spec.transport == "http" and not spec.url:
        errors.append(f"server {name}: http transport needs a url")
    if spec.transport == "stdio" and not (spec.package or spec.command):
        errors.append(f"server {name}: stdio transport needs a package or command")
    if spec.package and not (spec.version and EXACT_VERSION.match(spec.version)):
        errors.append(f"server {name}: {spec.package} must be pinned to an exact stable version")
    for arg in spec.args:
        if any(arg.startswith(bad) or bad in arg for bad in FORBIDDEN_ARGS):
            errors.append(f"server {name}: argument {arg!r} is not allowed")
    return errors


def _check_usage(
    profiles: McpProfiles,
    profile_name: str,
    profile: Profile,
    server_name: str,
    usage: ProfileServer,
    catalogs: dict[str, ToolCatalog],
) -> list[str]:
    where = f"profile {profile_name}, server {server_name}"
    spec = profiles.servers.get(server_name)
    if spec is None:
        return [f"{where}: unknown server"]
    errors: list[str] = []
    excluded = {e.name for e in profiles.never_read_only}
    if spec.package and usage.read_only is None:
        errors.append(f"{where}: declare read_only true or false for external servers")
    if usage.tools:
        catalog = catalogs.get(server_name)
        if catalog is None:
            return [*errors, f"{where}: tools are listed but the server has no pinned catalog"]
        if len(set(usage.tools)) != len(usage.tools):
            errors.append(f"{where}: duplicate tools")
        for tool in usage.tools:
            entry = catalog.get(tool)
            if entry is None:
                errors.append(f"{where}: {tool!r} is not in {spec.package}@{spec.version}")
            elif usage.read_only and (not entry.read_only or tool in excluded):
                errors.append(f"{where}: {tool!r} is not allowed in a read-only profile")
            elif entry.destructive:
                errors.append(f"{where}: destructive tool {tool!r} is never exposed")
    elif server_name in catalogs:
        errors.append(f"{where}: list the allowed tools explicitly")
    if usage.read_only is False and (profile.approval != "per-call" or profile.default):
        errors.append(f"{where}: write-capable profiles must be opt-in with per-call approval")
    return errors


def check_profiles(config_root: Path, repo_root: Path) -> list[str]:
    """Return every rule violation; an empty list means the profiles are valid."""
    profiles = load_profiles(config_root)
    errors: list[str] = []
    for name, spec in profiles.servers.items():
        errors += _check_server(name, spec)
    catalogs: dict[str, ToolCatalog] = {}
    for name, spec in profiles.servers.items():
        if spec.catalog:
            catalog = load_tool_catalog(config_root, spec.catalog)
            if (catalog.package, catalog.version) != (spec.package, spec.version):
                errors.append(f"server {name}: catalog is for {catalog.package}@{catalog.version}")
            catalogs[name] = catalog
    try:
        default = profiles.default_profile()
    except ValueError as error:
        return [*errors, str(error)]
    if (
        profiles.profiles[default].writes
        or profiles.profiles[default].execution_label is not ExecutionLabel.LOCAL
    ):
        errors.append(f"default profile {default}: must be LOCAL and read-only")
    for profile_name, profile in profiles.profiles.items():
        for server_name, usage in profile.servers.items():
            errors += _check_usage(profiles, profile_name, profile, server_name, usage, catalogs)
    project = repo_root / PROJECT_MCP_FILE
    expected = render(profiles, default, "claude")
    if not project.is_file() or json.loads(project.read_text(encoding="utf-8")) != expected:
        errors.append(
            f"{PROJECT_MCP_FILE} is stale; run "
            f"`ffia mcp render {default} --client claude --output {PROJECT_MCP_FILE}`"
        )
    return errors
