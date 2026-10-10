from pathlib import Path
from uuid import UUID

import pytest
from pydantic import SecretStr

from fabric_foundry_accelerator.config.bindings import (
    BindingsError,
    FoundryBinding,
    TenantBindings,
    WorkspaceBinding,
    export_environment,
    load_bindings,
)
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.services.foundry_readiness import project_endpoint


def _bindings() -> TenantBindings:
    return TenantBindings(
        tenant_id=str(UUID(int=1)),
        workspaces={
            "demo-dev": WorkspaceBinding(
                workspace_id=str(UUID(int=2)), semantic_models={"synthetic-model": str(UUID(int=4))}
            )
        },
        foundry=FoundryBinding(
            subscription_id=str(UUID(int=3)),
            resource_group="synthetic-dev",
            account="synthetic-foundry",
            project="synthetic-agents",
            model_deployments=("synthetic-model",),
            agents=("synthetic-agent",),
            fabric_connection="synthetic-fabric",
        ),
    )


def test_export_and_env_only_provider_bindings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("ENVIRONMENT", "FABRIC_LIVE", "FOUNDRY_LIVE", "ALLOW_LIVE_MUTATION"):
        monkeypatch.delenv(f"FFIA_{name}", raising=False)
    path = tmp_path / ".env"
    path.write_text("# retain this comment\nUNRELATED_SETTING=keep\n", encoding="utf-8")
    original = _bindings()
    keys = export_environment(original, path)
    export_environment(original, path)
    assert "FOUNDRY_PROJECT_ENDPOINT" in keys and "FABRIC_WORKSPACE_ID" in keys
    assert path.stat().st_mode & 0o777 == 0o600
    text = path.read_text(encoding="utf-8")
    assert text.count("\nAZURE_TENANT_ID=") == 1
    assert "UNRELATED_SETTING=keep" in text
    settings = Settings(_env_file=path)  # pyright: ignore[reportCallIssue]
    restored = load_bindings(tmp_path / "empty", "example-healthcare", settings=settings)
    assert restored == original
    assert original.tenant_id not in repr(settings)
    assert settings.foundry_project_endpoint is not None and original.foundry is not None
    assert settings.foundry_project_endpoint.get_secret_value() == project_endpoint(
        original.foundry
    )


def test_invalid_environment_bindings_do_not_echo_private_values(tmp_path: Path) -> None:
    private_value = "invalid-private-identifier"
    settings = Settings(_env_file=None, azure_tenant_id=SecretStr(private_value))  # pyright: ignore[reportCallIssue]
    with pytest.raises(BindingsError) as error:
        load_bindings(tmp_path, "example-healthcare", settings=settings)
    assert private_value not in str(error.value)


def test_export_refuses_symlink_and_incomplete_bindings(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_text("do not change", encoding="utf-8")
    path = tmp_path / ".env"
    path.symlink_to(target)
    with pytest.raises(BindingsError, match="symlink"):
        export_environment(_bindings(), path)
    assert target.read_text(encoding="utf-8") == "do not change"
    with pytest.raises(BindingsError, match="Foundry"):
        export_environment(TenantBindings(tenant_id=str(UUID(int=1))), tmp_path / ".env-other")
