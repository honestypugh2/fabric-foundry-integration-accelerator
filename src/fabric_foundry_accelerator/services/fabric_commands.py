"""``ffia fabric readiness``: read-only tenant readiness for the live labs."""

import argparse
import sys

from fabric_foundry_accelerator.config.bindings import load_bindings
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.providers.fabric.auth import AzureCliTokenProvider
from fabric_foundry_accelerator.providers.fabric.rest import FabricRestClient
from fabric_foundry_accelerator.services.fabric_readiness import ReadinessReport, run_readiness_sync


def print_report(report: ReadinessReport) -> None:
    """Print a readiness report as text."""
    for check in report.checks:
        sys.stdout.write(f"[{check.status:<7}] {check.name}: {check.detail}\n")
        if check.remediation:
            sys.stdout.write(f"          -> {check.remediation}\n")
    sys.stdout.write(f"\nFabric ready for live labs: {'YES' if report.ready else 'NO'}\n")


def _cmd_readiness(args: argparse.Namespace) -> int:
    settings = Settings()
    bindings = load_bindings(settings.config_root, settings.overlay, settings=settings)
    tenant_id = args.tenant or (bindings.tenant_id if bindings else None)
    if not tenant_id:
        sys.stderr.write(
            "No tenant to check. Pass --tenant <TENANT_ID> or create "
            f"config/customers/{settings.overlay}.local.yaml (git-ignored).\n"
        )
        return 2
    sys.stdout.write(
        "Read-only checks against the pinned tenant (Fabric REST GET requests; nothing is changed).\n"
    )
    report = run_readiness_sync(
        FabricRestClient(AzureCliTokenProvider(tenant_id)), bindings, tenant_id
    )
    if args.json:
        sys.stdout.write(report.model_dump_json(indent=2) + "\n")
    else:
        print_report(report)
    return 0 if report.ready else 1


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``fabric`` subcommands."""
    fabric = subparsers.add_parser("fabric", help="live Fabric tenant tools (read-only)")
    sub = fabric.add_subparsers(dest="fabric_command", required=True)
    readiness = sub.add_parser(
        "readiness", help="check the demo tenant is ready for live labs (read-only)"
    )
    readiness.add_argument("--tenant", help="tenant ID to check (default: the bindings file)")
    readiness.add_argument("--json", action="store_true")
    readiness.set_defaults(func=_cmd_readiness)
