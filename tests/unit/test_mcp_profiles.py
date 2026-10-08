"""MCP profiles: rendering per client and every safety rule in ``check_profiles``."""

import copy
import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml
from tests.conftest import CONFIG_ROOT, REPO_ROOT

from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.mcp.profiles import (
    check_profiles,
    launch_args,
    load_profiles,
    render,
    render_text,
)

BASE: dict[str, Any] = yaml.safe_load(
    (CONFIG_ROOT / "mcp" / "profiles.yaml").read_text(encoding="utf-8")
)


def test_committed_profiles_and_project_file_are_valid() -> None:
    assert check_profiles(CONFIG_ROOT, REPO_ROOT) == []
    profiles = load_profiles(CONFIG_ROOT)
    assert profiles.default_profile() == "offline"
    assert not profiles.profiles["offline"].writes
    assert profiles.profiles["fabric-authoring-gated"].writes


def test_launch_args_pin_and_narrow_the_server() -> None:
    profiles = load_profiles(CONFIG_ROOT)
    usage = profiles.profiles["fabric-docs"].servers["fabric-mcp"]
    command, args = launch_args(profiles.servers["fabric-mcp"], usage)
    assert command == "npx"
    assert args[:4] == ["-y", "@microsoft/fabric-mcp@1.4.0", "server", "start"]
    assert "--read-only" in args and args.count("--tool") == len(usage.tools) == 6
    gated = profiles.profiles["fabric-authoring-gated"].servers["fabric-mcp"]
    assert "--read-only" not in launch_args(profiles.servers["fabric-mcp"], gated)[1]


def test_render_shapes_per_client() -> None:
    profiles = load_profiles(CONFIG_ROOT)
    vscode = render(profiles, "offline", "vscode")
    assert set(vscode) == {"servers"}
    claude = render(profiles, "offline", "claude")
    assert (
        claude["mcpServers"]
        == json.loads((REPO_ROOT / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
    )
    cli: Any = render(profiles, "fabric-readonly", "copilot-cli")
    entry = cli["mcpServers"]["fabric-mcp"]
    assert entry["type"] == "local" and entry["tools"] == ["*"]
    assert cli is not None and render_text(profiles, "offline", "vscode").endswith("\n")
    with pytest.raises(KeyError, match="unknown MCP profile"):
        render(profiles, "nope", "vscode")


def _write(
    tmp_path: Path, data: dict[str, Any], *, project: dict[str, Any] | None = None
) -> tuple[Path, Path]:
    config = tmp_path / "config"
    (config / "mcp").mkdir(parents=True)
    shutil.copytree(CONFIG_ROOT / "mcp" / "catalog", config / "mcp" / "catalog")
    (config / "mcp" / "profiles.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    if project is None:
        project = render(load_profiles(CONFIG_ROOT), "offline", "claude")
    (tmp_path / ".mcp.json").write_text(json.dumps(project), encoding="utf-8")
    return config, tmp_path


Mutation = Callable[[dict[str, Any]], None]


def _set(path: str, value: object) -> Mutation:
    def apply(data: dict[str, Any]) -> None:
        *parents, leaf = path.split(".")
        node = data
        for key in parents:
            node = node[key]
        node[leaf] = value

    return apply


def _readonly_tools(*tools: str) -> Mutation:
    return _set("profiles.fabric-readonly.servers.fabric-mcp.tools", list(tools))


@pytest.mark.parametrize(
    ("mutation", "fragment"),
    [
        (_set("servers.fabric-mcp.version", "latest"), "exact stable version"),
        (_set("servers.fabric-mcp.version", "2.0.0-beta.1"), "exact stable version"),
        (
            _set(
                "servers.fabric-mcp.args", ["server", "start", "--dangerously-disable-retry-limits"]
            ),
            "not allowed",
        ),
        (_set("servers.powerbi-modeling-mcp.args", ["--start", "--accept-eula"]), "not allowed"),
        (_set("servers.microsoft-learn.url", None), "needs a url"),
        (_set("servers.ffia-local.command", None), "needs a package or command"),
        (_readonly_tools("core_create-item"), "not allowed in a read-only profile"),
        (_readonly_tools("datafactory_execute-query"), "not allowed in a read-only profile"),
        (_readonly_tools("onelake_download-file"), "not allowed in a read-only profile"),
        (_readonly_tools("onelake_list-tables", "onelake_list-tables"), "duplicate tools"),
        (_readonly_tools("imaginary_tool"), "is not in @microsoft/fabric-mcp@1.4.0"),
        (_readonly_tools(), "list the allowed tools explicitly"),
        (
            _set(
                "profiles.fabric-authoring-gated.servers.fabric-mcp.tools", ["onelake_delete-file"]
            ),
            "destructive tool",
        ),
        (_set("profiles.fabric-authoring-gated.approval", "none"), "per-call approval"),
        (_set("profiles.fabric-readonly.servers.fabric-mcp.read_only", None), "declare read_only"),
        (_set("profiles.fabric-docs.servers.nope", {}), "unknown server"),
        (_set("profiles.offline.servers.ffia-local", {"tools": ["x"]}), "no pinned catalog"),
        (_set("profiles.offline.execution_label", "LIVE"), "must be LOCAL and read-only"),
        (_set("profiles.fabric-docs.default", True), "exactly one default profile"),
    ],
)
def test_rule_violations_are_reported(tmp_path: Path, mutation: Mutation, fragment: str) -> None:
    data = copy.deepcopy(BASE)
    mutation(data)
    errors = check_profiles(*_write(tmp_path, data))
    assert any(fragment in e for e in errors), errors


def test_catalog_must_match_the_pin(tmp_path: Path) -> None:
    config, root = _write(tmp_path, copy.deepcopy(BASE))
    catalog = config / "mcp" / "catalog" / "fabric-mcp-1.4.0.yaml"
    catalog.write_text(
        catalog.read_text(encoding="utf-8").replace("version: 1.4.0", "version: 1.3.0"),
        encoding="utf-8",
    )
    assert any("catalog is for" in e for e in check_profiles(config, root))


def test_stale_project_file_is_reported(tmp_path: Path) -> None:
    errors = check_profiles(*_write(tmp_path, copy.deepcopy(BASE), project={"mcpServers": {}}))
    assert errors == [
        ".mcp.json is stale; run `ffia mcp render offline --client claude --output .mcp.json`"
    ]


def test_mcp_cli(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    assert main(["mcp", "profiles"]) == 0
    out = capsys.readouterr().out
    assert (
        "fabric-readonly" in out and "16 allow-listed tools" in out and "per-call approval" in out
    )
    assert main(["mcp", "render", "fabric-docs", "--client", "claude"]) == 0
    assert "@microsoft/fabric-mcp@1.4.0" in capsys.readouterr().out
    target = tmp_path / "mcp.json"
    assert main(["mcp", "render", "offline", "--output", str(target)]) == 0
    assert "servers" in json.loads(target.read_text(encoding="utf-8"))
    assert main(["mcp", "check"]) == 0
    assert "MCP profiles: OK" in capsys.readouterr().out

    data = copy.deepcopy(BASE)
    _set("servers.fabric-mcp.version", "latest")(data)
    config, root = _write(tmp_path / "bad", data)
    monkeypatch.chdir(root)
    monkeypatch.setenv("FFIA_CONFIG_ROOT", str(config))
    assert main(["mcp", "check"]) == 1
    assert "exact stable version" in capsys.readouterr().err
