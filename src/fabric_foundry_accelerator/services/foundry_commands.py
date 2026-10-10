"""``ffia foundry readiness``: read-only Foundry project readiness for the agent demos."""

import argparse
import sys

from fabric_foundry_accelerator.config.bindings import load_bindings
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.providers.fabric.auth import AzureCliTokenProvider
from fabric_foundry_accelerator.services.foundry_readiness import FoundryReadiness, run_sync


def _cmd_readiness(args: argparse.Namespace) -> int:
    settings = Settings()
    bindings = load_bindings(settings.config_root, settings.overlay, settings=settings)
    if bindings is None or bindings.foundry is None:
        sys.stderr.write(
            "No Foundry binding. Add a `foundry:` section to "
            f"config/customers/{settings.overlay}.local.yaml (git-ignored); see the .local.example.yaml.\n"
        )
        return 2
    sys.stdout.write(
        "Read-only checks (Azure Resource Manager and Foundry project GET requests; nothing is changed).\n"
    )
    report = run_sync(FoundryReadiness(AzureCliTokenProvider(bindings.tenant_id)), bindings.foundry)
    if args.json:
        sys.stdout.write(report.model_dump_json(indent=2) + "\n")
    else:
        for check in report.checks:
            sys.stdout.write(f"[{check.status:<7}] {check.name}: {check.detail}\n")
            if check.remediation:
                sys.stdout.write(f"          -> {check.remediation}\n")
        sys.stdout.write(f"\nFoundry ready for agent demos: {'YES' if report.ready else 'NO'}\n")
    return 0 if report.ready else 1


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``foundry`` subcommands."""
    foundry = subparsers.add_parser("foundry", help="Microsoft Foundry project tools (read-only)")
    sub = foundry.add_subparsers(dest="foundry_command", required=True)
    readiness = sub.add_parser("readiness", help="check the Foundry project is ready (read-only)")
    readiness.add_argument("--json", action="store_true")
    readiness.set_defaults(func=_cmd_readiness)
