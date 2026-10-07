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
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.education.guides import UseCaseGuide
from fabric_foundry_accelerator.models.changes import ChangeRequest, ProposedChange
from fabric_foundry_accelerator.models.semantic import SemanticModel
from fabric_foundry_accelerator.observability.logging import configure_logging
from fabric_foundry_accelerator.patterns.catalog import PatternCatalog
from fabric_foundry_accelerator.policies.engine import ToolManifest, WritePolicy
from fabric_foundry_accelerator.services.container import build_container
from fabric_foundry_accelerator.services.demo import demo_check, run_offline_demo

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
}
DEFAULT_SCHEMA_DIR = Path("schemas")


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
    container = build_container(Settings())
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


def _cmd_serve_api(args: argparse.Namespace) -> int:
    import uvicorn  # noqa: PLC0415 - server dependency only needed for this command

    from fabric_foundry_accelerator.api.app import create_app  # noqa: PLC0415

    settings = Settings()
    configure_logging(level=settings.log_level, json=settings.log_json)
    uvicorn.run(
        create_app(build_container(settings)), host=args.host, port=args.port, log_level="info"
    )
    return 0


def _cmd_serve_mcp(_: argparse.Namespace) -> int:
    from fabric_foundry_accelerator.mcp.server import build_mcp_server  # noqa: PLC0415

    settings = Settings()
    configure_logging(level=settings.log_level, json=True)
    build_mcp_server(build_container(settings)).run(transport="stdio", show_banner=False)
    return 0


def render_schemas() -> dict[str, str]:
    """Render every public model's JSON Schema."""
    return {
        name: json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
        for name, model in SCHEMA_MODELS.items()
    }


def _cmd_schemas_export(args: argparse.Namespace) -> int:
    directory = Path(args.dir)
    directory.mkdir(parents=True, exist_ok=True)
    for name, text in render_schemas().items():
        (directory / f"{name}.schema.json").write_text(text, encoding="utf-8")
    _out(f"exported {len(SCHEMA_MODELS)} schemas to {directory}")
    return 0


def _cmd_schemas_check(args: argparse.Namespace) -> int:
    directory = Path(args.dir)
    stale = [
        name
        for name, text in render_schemas().items()
        if not (directory / f"{name}.schema.json").is_file()
        or (directory / f"{name}.schema.json").read_text(encoding="utf-8") != text
    ]
    for name in stale:
        _err(f"{name}.schema.json is stale; run `ffia schemas export`")
    if not stale:
        _out(f"{len(SCHEMA_MODELS)} schemas are up to date")
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

    serve = subparsers.add_parser("serve", help="run the API or the local MCP server")
    serve_sub = serve.add_subparsers(dest="serve_command", required=True)
    api = serve_sub.add_parser("api", help="FastAPI control plane (loopback by default)")
    api.add_argument("--host", default="127.0.0.1")
    api.add_argument("--port", type=int, default=8000)
    api.set_defaults(func=_cmd_serve_api)
    serve_sub.add_parser("mcp", help="local educational MCP server over stdio").set_defaults(
        func=_cmd_serve_mcp
    )

    schemas = subparsers.add_parser("schemas", help="JSON Schemas for public models")
    schemas_sub = schemas.add_subparsers(dest="schemas_command", required=True)
    for name, func, text in (
        ("export", _cmd_schemas_export, "write schemas/"),
        ("check", _cmd_schemas_check, "fail if schemas/ is stale"),
    ):
        command = schemas_sub.add_parser(name, help=text)
        command.add_argument("--dir", default=str(DEFAULT_SCHEMA_DIR))
        command.set_defaults(func=func)
