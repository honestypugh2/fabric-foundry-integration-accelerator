"""Harness permissions as code: one policy, three clients, and an enforced Claude Code guard."""

import io
import json
import shutil
from pathlib import Path

import pytest
from tests.conftest import CONFIG_ROOT, REPO_ROOT

from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.harness.policy import (
    GUARD_COMMAND,
    check,
    evaluate_command,
    guard_hook_output,
    load_policy,
    render,
    render_copilot_cli,
    render_vscode,
)
from fabric_foundry_accelerator.providers.errors import UnknownResourceError

POLICY = load_policy(CONFIG_ROOT)


def test_committed_settings_match_the_repo_profile() -> None:
    assert check(POLICY, REPO_ROOT) == []
    claude = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    permissions = claude["permissions"]
    assert permissions["disableBypassPermissionsMode"] == "disable"
    assert "Bash(az rest:*)" in permissions["ask"]
    assert "Read(./**/*.local.yaml)" in permissions["deny"]
    assert "Edit" not in permissions["allow"], "the repo profile does not pre-approve edits"
    assert claude["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == GUARD_COMMAND
    with pytest.raises(UnknownResourceError):
        POLICY.profile("nope")


def test_bakeoff_profile_renders_identically_for_every_model() -> None:
    args = render_copilot_cli(POLICY.profile("bakeoff"))
    pairs = list(zip(args[::2], args[1::2], strict=True))
    allowed = {v for k, v in pairs if k == "--allow-tool"}
    denied = {v for k, v in pairs if k == "--deny-tool"}
    assert {"write", "ffia-local", "shell(ffia:*)", "shell(git diff)"} <= allowed
    assert {
        "shell(az:*)",
        "shell(git push)",
        "shell(rm:*)",
        "fabric-mcp(core_create-item)",
    } <= denied
    claude = json.dumps(render(POLICY, "bakeoff", "claude"))
    assert '"Bash(az:*)"' in claude
    vscode = render_vscode(POLICY.profile("bakeoff"))
    assert vscode["/^az\\b/"] is False and vscode["/^git\\s+push\\b/"] is False


def test_check_reports_stale_files_and_contradictions(tmp_path: Path) -> None:
    errors = check(POLICY, tmp_path)
    assert any(".claude/settings.json is stale" in e for e in errors)
    assert any("autoApprove is stale" in e for e in errors)
    profile = POLICY.profile("bakeoff")
    bad = POLICY.model_copy(
        update={
            "profiles": {
                **POLICY.profiles,
                "bakeoff": profile.model_copy(
                    update={"shell": profile.shell.model_copy(update={"deny": ("ffia",)})}
                ),
            }
        }
    )
    assert any("both allowed and denied" in e for e in check(bad, REPO_ROOT))


@pytest.mark.parametrize(
    "command",
    [
        "az fabric capacity suspend -g rg -n cap",
        "az resource invoke-action --action suspend --ids x",
        "cd x && az account set --subscription other",
        "az group delete -n rg --yes",
        "az account get-access-token --resource https://api.fabric.microsoft.com",
        "git push --force origin main",
        "git push -f",
        "rm -rf /",
        "rm -rf ~",
        "sudo rm -rf ..",
        "cat .env.local",
        "grep tenant config/customers/example-healthcare.local.yaml",
    ],
)
def test_guard_blocks(command: str) -> None:
    assert evaluate_command(command).denied, command


@pytest.mark.parametrize(
    "command",
    [
        "ffia data build --profile hc-lab-7file-v1",
        "az account show --query name",
        "az rest --method get --url https://api.fabric.microsoft.com/v1/workspaces",
        "git push origin feature",
        "rm -rf build/",
        "cat README.md",
        "grep -r local_sales_query src",
    ],
)
def test_guard_allows(command: str) -> None:
    assert not evaluate_command(command).denied, command


def test_guard_hook_protocol() -> None:
    denied = guard_hook_output(
        json.dumps({"tool_name": "Bash", "tool_input": {"command": "az group delete -n x"}})
    )
    assert denied is not None
    output = json.loads(denied)["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse" and output["permissionDecision"] == "deny"
    assert "governed change flow" in output["permissionDecisionReason"]
    for payload in (
        json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}),
        json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "x"}}),
        json.dumps([1, 2]),
        "not json",
    ):
        assert guard_hook_output(payload) is None


def test_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    assert main(["harness", "check"]) == 0
    assert main(["harness", "render", "bakeoff", "--client", "copilot-cli"]) == 0
    assert "--deny-tool 'shell(az:*)'" in capsys.readouterr().out
    assert main(["harness", "render", "repo"]) == 0
    assert '"disableBypassPermissionsMode": "disable"' in capsys.readouterr().out
    assert main(["harness", "render", "repo", "--client", "vscode"]) == 0
    assert "/^az\\\\s+rest\\\\b/" in capsys.readouterr().out
    argv = tmp_path / "argv.json"
    assert (
        main(["harness", "render", "bakeoff", "--client", "copilot-cli", "--output", str(argv)])
        == 0
    )
    assert "--allow-tool" in json.loads(argv.read_text(encoding="utf-8"))
    vscode = tmp_path / "settings.json"
    vscode.write_text(json.dumps({"editor.tabSize": 2}), encoding="utf-8")
    assert main(["harness", "render", "repo", "--client", "vscode", "--output", str(vscode)]) == 0
    merged = json.loads(vscode.read_text(encoding="utf-8"))
    assert merged["editor.tabSize"] == 2 and "chat.tools.terminal.autoApprove" in merged

    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push --force"}})
        ),
    )
    assert main(["harness", "guard"]) == 0
    assert '"permissionDecision": "deny"' in capsys.readouterr().out
    monkeypatch.setattr(
        "sys.stdin", io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}))
    )
    assert main(["harness", "guard"]) == 0
    assert capsys.readouterr().out == ""

    stale = tmp_path / "repo"
    shutil.copytree(REPO_ROOT / "config" / "harness", stale / "config" / "harness")
    monkeypatch.chdir(stale)
    monkeypatch.setenv("FFIA_CONFIG_ROOT", str(stale / "config"))
    assert main(["harness", "check"]) == 1
    assert "is stale" in capsys.readouterr().err
