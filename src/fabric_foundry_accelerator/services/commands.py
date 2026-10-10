"""``ffia demo``, ``ffia serve`` and ``ffia schemas`` subcommands."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from pydantic import BaseModel

from fabric_foundry_accelerator.audit.store import AuditRecord
from fabric_foundry_accelerator.config.environment import EnvironmentConfiguration
from fabric_foundry_accelerator.config.overlay import CustomerOverlay
from fabric_foundry_accelerator.config.settings import ApiSettings, Settings
from fabric_foundry_accelerator.education.guides import UseCaseGuide
from fabric_foundry_accelerator.education.lessons import (
    ArchitectureMap,
    ChecksFile,
    Completeness,
    Lab,
    LessonMeta,
)
from fabric_foundry_accelerator.models.changes import ChangeRequest, ProposedChange
from fabric_foundry_accelerator.models.semantic import SemanticModel
from fabric_foundry_accelerator.observability.logging import configure_logging
from fabric_foundry_accelerator.observability.tracing import configure_tracing
from fabric_foundry_accelerator.patterns.catalog import PatternCatalog
from fabric_foundry_accelerator.policies.engine import ToolManifest, WritePolicy
from fabric_foundry_accelerator.services.container import build_container
from fabric_foundry_accelerator.services.demo import (
    demo_check,
    run_connected_demo,
    run_offline_demo,
)

SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "customer-overlay": CustomerOverlay,
    "environment-configuration": EnvironmentConfiguration,
    "use-case-guide": UseCaseGuide,
    "pattern-catalog": PatternCatalog,
    "tool-manifest": ToolManifest,
    "write-policy": WritePolicy,
    "semantic-model": SemanticModel,
    "change-request": ChangeRequest,
    "proposed-change": ProposedChange,
    "audit-record": AuditRecord,
    "lesson": LessonMeta,
    "knowledge-checks": ChecksFile,
    "lab": Lab,
    "architecture-map": ArchitectureMap,
    "completeness": Completeness,
}
DEFAULT_SCHEMA_DIR = Path("schemas")
DEFAULT_TYPESCRIPT_PATH = Path("frontend/src/api/generated.ts")


def _out(message: str) -> None:
    sys.stdout.write(f"{message}\n")


def _err(message: str) -> None:
    sys.stderr.write(f"{message}\n")


def _cmd_demo_check(args: argparse.Namespace) -> int:
    container = build_container(Settings(audit_path=None))
    report = asyncio.run(demo_check(container, azure_probe=not args.no_azure_cli))
    if args.json:
        _out(report.model_dump_json(indent=2))
        return 0
    width = max(len(line.component) for line in report.lines) + 2
    for line in report.lines:
        _out(f"{line.component + ':':<{width}} {line.status:<15} {line.detail}")
    _out("")
    _out(f"Recommended Mode: {report.recommended_mode}")
    _out(f"Reason: {report.reason}")
    return 0


def _cmd_demo_offline(args: argparse.Namespace) -> int:
    container = build_container(
        Settings(
            environment="offline", fabric_live=False, foundry_live=False, allow_live_mutation=False
        )
    )
    report = asyncio.run(run_offline_demo(container, work_dir=Path(args.work_dir)))
    if args.json:
        _out(report.model_dump_json(indent=2))
        return 0 if report.passed else 1

    _out(
        f"OFFLINE DEMO ({report.operating_mode}) - every result is labeled; nothing is presented as a cloud operation."
    )
    for step in report.steps:
        verdict = "PASS" if step.passed else ("FAIL" if step.required else "SKIP")
        _out(f"[{verdict}] ACT {step.act:>2} [{step.label}] {step.title}")
        _out(f"           {step.summary}")
        for item in step.evidence:
            if item:
                _out(f"           - {item}")
    _out("")
    _out(
        f"Labels: {report.label_counts} | LIVE operations: {report.live_operations} | "
        f"cloud operations: {report.cloud_operations}"
    )
    _out(f"Release gate: {'PASSED' if report.passed else 'FAILED'}")
    return 0 if report.passed else 1


def _cmd_demo_connected(args: argparse.Namespace) -> int:
    settings = ApiSettings(
        environment=args.demo_command,
        fabric_live=True,
        foundry_live=True,
        allow_live_mutation=False,
    )
    configure_logging(level=settings.log_level, json=settings.log_json)
    _err(
        "Provider/server/tools: application Fabric REST list_workspaces; "
        "Foundry project's Responses SDK, one synthetic evaluation question (not MCP). "
        "No Fabric write or message delivery; model usage may incur cost."
    )
    report = asyncio.run(run_connected_demo(build_container(settings)))
    if args.json:
        _out(report.model_dump_json(indent=2))
    else:
        for step in report.steps:
            _out(
                f"[{'PASS' if step.passed else 'FAIL'}] [{step.label}] {step.title}: {step.summary}"
            )
            for evidence in step.evidence:
                _out(f"  {evidence}")
        _out(f"Demo passed: {report.passed}; live path verified: {report.live_verified}")
    return 0 if report.passed else 1


def _cmd_serve_api(args: argparse.Namespace) -> int:
    import uvicorn  # noqa: PLC0415 - server dependency only needed for this command

    from fabric_foundry_accelerator.api.app import create_app  # noqa: PLC0415

    settings = (
        Settings(
            environment="offline", fabric_live=False, foundry_live=False, allow_live_mutation=False
        )
        if args.offline
        else ApiSettings()
    )
    configure_logging(level=settings.log_level, json=settings.log_json)
    sys.stderr.write(configure_tracing(settings.applicationinsights_connection_string) + "\n")
    uvicorn.run(
        create_app(build_container(settings)), host=args.host, port=args.port, log_level="info"
    )
    return 0


def _cmd_serve_mcp(_: argparse.Namespace) -> int:
    from fabric_foundry_accelerator.mcp.server import build_mcp_server  # noqa: PLC0415

    settings = Settings(
        environment="offline", fabric_live=False, foundry_live=False, allow_live_mutation=False
    )
    configure_logging(level=settings.log_level, json=True)
    build_mcp_server(build_container(settings)).run(transport="stdio", show_banner=False)
    return 0


def render_schemas() -> dict[str, str]:
    """Render every public model's JSON Schema."""
    return {
        name: json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
        for name, model in SCHEMA_MODELS.items()
    }


def render_artifacts(schema_dir: Path, typescript_path: Path) -> dict[Path, str]:
    """Render JSON Schemas, the OpenAPI document and the frontend's generated TypeScript types."""
    from fabric_foundry_accelerator.api.app import openapi_document  # noqa: PLC0415
    from fabric_foundry_accelerator.api.typescript import render_typescript  # noqa: PLC0415

    artifacts = {
        schema_dir / f"{name}.schema.json": text for name, text in render_schemas().items()
    }
    document = openapi_document()
    artifacts[schema_dir / "openapi.json"] = json.dumps(document, indent=2, sort_keys=True) + "\n"
    artifacts[typescript_path] = render_typescript(document)
    return artifacts


def _cmd_schemas_export(args: argparse.Namespace) -> int:
    artifacts = render_artifacts(Path(args.dir), Path(args.typescript))
    for path, text in artifacts.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _out(f"exported {len(artifacts)} artifacts (JSON Schemas, OpenAPI, TypeScript types)")
    return 0


def _cmd_schemas_check(args: argparse.Namespace) -> int:
    artifacts = render_artifacts(Path(args.dir), Path(args.typescript))
    stale = [
        path
        for path, text in artifacts.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != text
    ]
    for path in stale:
        _err(f"{path} is stale; run `ffia schemas export`")
    if not stale:
        _out(f"{len(artifacts)} artifacts are up to date")
    return 1 if stale else 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``demo``, ``serve`` and ``schemas`` subcommands."""
    demo = subparsers.add_parser("demo", help="demo readiness and the offline demo")
    demo_sub = demo.add_subparsers(dest="demo_command", required=True)
    check = demo_sub.add_parser(
        "check", help="probe components and recommend LIVE, HYBRID or OFFLINE"
    )
    check.add_argument("--json", action="store_true")
    check.add_argument(
        "--no-azure-cli", action="store_true", help="skip the local Azure CLI cache check"
    )
    check.set_defaults(func=_cmd_demo_check)
    offline = demo_sub.add_parser("offline", help="run the ten-act offline demo (release gate)")
    offline.add_argument("--json", action="store_true")
    offline.add_argument("--work-dir", default="data/runtime/demo")
    offline.set_defaults(func=_cmd_demo_offline)
    for mode in ("live", "hybrid"):
        connected = demo_sub.add_parser(
            mode, help="bounded Fabric read + one synthetic agent question"
        )
        connected.add_argument("--json", action="store_true")
        connected.set_defaults(func=_cmd_demo_connected)

    serve = subparsers.add_parser("serve", help="run the API or the local MCP server")
    serve_sub = serve.add_subparsers(dest="serve_command", required=True)
    api = serve_sub.add_parser("api", help="FastAPI control plane (loopback by default)")
    api.add_argument("--host", default="127.0.0.1")
    api.add_argument("--port", type=int, default=8000)
    api.add_argument(
        "--offline", action="store_true", help="disable cloud providers for both guides"
    )
    api.set_defaults(func=_cmd_serve_api)
    serve_sub.add_parser("mcp", help="local educational MCP server over stdio").set_defaults(
        func=_cmd_serve_mcp
    )

    schemas = subparsers.add_parser("schemas", help="JSON Schemas for public models")
    schemas_sub = schemas.add_subparsers(dest="schemas_command", required=True)
    for name, func, text in (
        ("export", _cmd_schemas_export, "write schemas/ and the frontend API types"),
        ("check", _cmd_schemas_check, "fail if schemas/ or the frontend API types are stale"),
    ):
        command = schemas_sub.add_parser(name, help=text)
        command.add_argument("--dir", default=str(DEFAULT_SCHEMA_DIR))
        command.add_argument("--typescript", default=str(DEFAULT_TYPESCRIPT_PATH))
        command.set_defaults(func=func)
