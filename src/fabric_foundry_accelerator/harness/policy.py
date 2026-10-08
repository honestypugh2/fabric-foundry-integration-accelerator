"""Harness permissions as code: one policy rendered for Claude Code, Copilot CLI and VS Code.

The same rule ("deny `az`", "ask before `az rest`", "deny the Fabric MCP delete tool") is written
once in ``config/harness/policy.yaml`` and rendered into each client's own syntax:

* Claude Code: ``.claude/settings.json`` ``permissions`` (``Bash(x:*)``, ``Read(./x)``,
  ``mcp__server__tool``), ``disableBypassPermissionsMode`` and a ``PreToolUse`` hook that runs
  ``ffia harness guard``;
* GitHub Copilot CLI: ``--allow-tool`` / ``--deny-tool`` arguments (``shell(x:*)``,
  ``server(tool)``, ``write``);
* VS Code (Copilot agent mode): ``chat.tools.terminal.autoApprove`` entries set to ``false`` so a
  person approves each matching command.

Deny always wins over allow and ask in every client. Permissions are not authority: they only
decide which calls an agent may attempt without a person.
"""

import json
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.providers.errors import UnknownResourceError

POLICY_FILE = Path("harness") / "policy.yaml"
HarnessClient = Literal["claude", "copilot-cli", "vscode"]
CLAUDE_SETTINGS = Path(".claude") / "settings.json"
VSCODE_SETTINGS = Path(".vscode") / "settings.json"
VSCODE_KEY = "chat.tools.terminal.autoApprove"
GUARD_COMMAND = 'cd "$CLAUDE_PROJECT_DIR" && uv run --frozen ffia harness guard'
# Copilot CLI approves git and gh on a first-level subcommand basis ("git push").
_SUBCOMMAND_TOOLS = ("git", "gh")


class ShellRules(BaseModel):
    """Command prefixes (words)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    allow: tuple[str, ...] = ()
    ask: tuple[str, ...] = ()
    deny: tuple[str, ...] = ()


class McpRules(BaseModel):
    """Servers to allow, and ``server:tool`` pairs to deny."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    allow: tuple[str, ...] = ()
    deny: tuple[str, ...] = ()


class HarnessProfile(BaseModel):
    """One permission profile."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    description: str
    write: bool
    shell: ShellRules
    read_deny: tuple[str, ...] = ()
    mcp: McpRules = McpRules()
    guard: bool = True


class HarnessPolicy(BaseModel):
    """``config/harness/policy.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    profiles: dict[str, HarnessProfile] = Field(min_length=1)

    def profile(self, name: str) -> HarnessProfile:
        """Return a profile by name.

        Raises:
            UnknownResourceError: no such profile.
        """
        found = self.profiles.get(name)
        if found is None:
            raise UnknownResourceError(
                f"unknown harness profile {name!r}; choose from {sorted(self.profiles)}"
            )
        return found


def load_policy(config_root: Path) -> HarnessPolicy:
    """Load the harness policy."""
    path = config_root / POLICY_FILE
    return HarnessPolicy.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def _mcp_pair(entry: str) -> tuple[str, str]:
    server, _, tool = entry.partition(":")
    return server, tool


def render_claude(profile: HarnessProfile) -> dict[str, object]:
    """``.claude/settings.json`` for Claude Code."""
    allow = [f"Bash({p}:*)" for p in profile.shell.allow]
    if profile.write:
        allow += ["Edit", "Write"]
    allow += [f"mcp__{server}" for server in profile.mcp.allow]
    deny = [f"Bash({p}:*)" for p in profile.shell.deny]
    deny += [f"Read(./{glob})" for glob in profile.read_deny]
    deny += [f"mcp__{s}__{t}" for s, t in map(_mcp_pair, profile.mcp.deny)]
    settings: dict[str, object] = {
        "$schema": "https://json.schemastore.org/claude-code-settings.json",
        "permissions": {
            "allow": allow,
            "ask": [f"Bash({p}:*)" for p in profile.shell.ask],
            "deny": deny,
            "disableBypassPermissionsMode": "disable",
        },
    }
    if profile.guard:
        settings["hooks"] = {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": GUARD_COMMAND}]}
            ]
        }
    return settings


def _copilot_shell(prefix: str) -> str:
    words = prefix.split()
    if len(words) == 2 and words[0] in _SUBCOMMAND_TOOLS:
        return f"shell({prefix})"
    return f"shell({prefix}:*)"


def render_copilot_cli(profile: HarnessProfile) -> list[str]:
    """Arguments for ``copilot`` (CLI). Ask rules are simply not pre-approved."""
    args: list[str] = []
    allowed = [_copilot_shell(p) for p in profile.shell.allow]
    if profile.write:
        allowed.append("write")
    allowed += list(profile.mcp.allow)
    for rule in allowed:
        args += ["--allow-tool", rule]
    denied = [_copilot_shell(p) for p in profile.shell.deny]
    denied += [f"{s}({t})" for s, t in map(_mcp_pair, profile.mcp.deny)]
    for rule in denied:
        args += ["--deny-tool", rule]
    return args


def _vscode_regex(prefix: str) -> str:
    return "/^" + r"\s+".join(re.escape(word) for word in prefix.split()) + r"\b/"


def render_vscode(profile: HarnessProfile) -> dict[str, bool]:
    """``chat.tools.terminal.autoApprove`` entries: ask and deny both require a person."""
    return {_vscode_regex(p): False for p in (*profile.shell.ask, *profile.shell.deny)}


def render(policy: HarnessPolicy, name: str, client: HarnessClient) -> object:
    """Render one profile for one client."""
    profile = policy.profile(name)
    if client == "claude":
        return render_claude(profile)
    if client == "copilot-cli":
        return render_copilot_cli(profile)
    return render_vscode(profile)


def check(policy: HarnessPolicy, repo_root: Path) -> list[str]:
    """The committed Claude Code and VS Code settings must equal the ``repo`` profile render."""
    errors: list[str] = []
    claude_path = repo_root / CLAUDE_SETTINGS
    expected = render(policy, "repo", "claude")
    if not claude_path.is_file() or json.loads(claude_path.read_text(encoding="utf-8")) != expected:
        errors.append(
            f"{CLAUDE_SETTINGS} is stale; run `ffia harness render repo --client claude "
            f"--output {CLAUDE_SETTINGS}`"
        )
    vscode_path = repo_root / VSCODE_SETTINGS
    settings: object = (
        json.loads(vscode_path.read_text(encoding="utf-8")) if vscode_path.is_file() else {}
    )
    actual = settings.get(VSCODE_KEY) if isinstance(settings, dict) else None  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if actual != render(policy, "repo", "vscode"):
        errors.append(
            f"{VSCODE_SETTINGS} {VSCODE_KEY} is stale; run `ffia harness render repo --client vscode`"
        )
    for name, profile in policy.profiles.items():
        overlap = set(profile.shell.allow) & set(profile.shell.deny)
        if overlap:
            errors.append(f"profile {name}: {sorted(overlap)} are both allowed and denied")
    return errors


# ------------------------------------------------------------------ guard (Claude Code hook)
_GUARDS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\baz\s+(?:[\w-]+\s+)*?(?:create|delete|update|set|remove|purge|deploy|"
            r"invoke-action|start|stop|suspend|resume|restart|assign)\b"
        ),
        "Azure changes go through the governed change flow (PLAN, APPROVE, EXECUTE), never an "
        "agent's az command.",
    ),
    (
        re.compile(r"\b(?:get-access-token|account\s+show\s+.*--show-token)\b"),
        "Printing tokens is never allowed.",
    ),
    (
        re.compile(r"\bgit\s+push\b.*(?:--force\b|-f\b|--force-with-lease\b)"),
        "Force-push rewrites shared history.",
    ),
    (
        re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?[a-zA-Z]*\s+(?:/|~|\$HOME|\.\.)(?:\s|/?$)"),
        "Recursive delete of the root, home or a parent folder.",
    ),
    (
        re.compile(
            r"\b(?:cat|less|more|head|tail|grep|sed|awk)\b[^|;&]*(?:\.env\b|\.local\.(?:yaml|json)\b)"
        ),
        "Secret and environment-identifier files stay out of agent context.",
    ),
)


class GuardDecision(BaseModel):
    """The hook's decision for one Bash command."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    denied: bool
    reason: str


def evaluate_command(command: str) -> GuardDecision:
    """Deny a command that matches any guard pattern anywhere in it (compound commands too)."""
    for pattern, reason in _GUARDS:
        if pattern.search(command):
            return GuardDecision(denied=True, reason=reason)
    return GuardDecision(denied=False, reason="")


def guard_hook_output(payload: str) -> str | None:
    """Claude Code PreToolUse hook: JSON to print when denied, ``None`` for no decision."""
    try:
        data: object = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    tool_input: object = data.get("tool_input")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    command: object = tool_input.get("command") if isinstance(tool_input, dict) else None  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if data.get("tool_name") != "Bash" or not isinstance(command, str):  # pyright: ignore[reportUnknownMemberType]
        return None
    decision = evaluate_command(command)
    if not decision.denied:
        return None
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Blocked by ffia harness guard: {decision.reason}",
            }
        }
    )
