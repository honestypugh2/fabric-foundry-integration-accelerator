"""``ffia mfg quality | brief``: the offline (LOCAL) side of the Foundry + Fabric workshop.

Builds the synthetic manufacturing profile with DuckDB and prints what the live demo shows from
Fabric and Foundry: data-quality findings with proposed corrections, and each business team's
monthly brief. Results are LOCAL; no cloud call is made.
"""

import argparse
import json
import sys

from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.synthetic.manufacturing import INJECTED, MFG_PROFILES, TEAMS, build

PROFILE = "mfg-sales-v1"
FIXES: dict[str, str] = {
    "duplicate_order_lines": "Keep one copy per (order_id, line_number) in Silver; report the source system.",
    "orphan_product_ids": "Map retired product codes to their successors, or add them to the product master.",
    "negative_quantity_shipped": "Route to returns processing; exclude from booked revenue until confirmed.",
    "unit_price_outliers": "Prices entered per box (100x): divide by pack size after steward review.",
    "future_order_dates": "Hold until the order date arrives; check the ERP date entry.",
    "shipped_without_ship_date": "Backfill from the shipping system or set status to Open.",
    "ship_before_order": "Correct the order or ship date in the ERP; exclude until fixed.",
    "missing_customer_region": "Assign region from the customer's ship-to address.",
    "nonstandard_region_labels": "Standardize labels with the region mapping table in Silver.",
}
LABEL = "LOCAL (synthetic data on this machine; no Fabric or Foundry call)"


def _cmd_quality(args: argparse.Namespace) -> int:
    settings = Settings()
    result = build(settings.data_root / "raw" / PROFILE, MFG_PROFILES[PROFILE])
    if args.json:
        sys.stdout.write(
            json.dumps({"label": "LOCAL", "data_quality": result.data_quality}, indent=2) + "\n"
        )
        return 0
    sys.stdout.write(f"Data-quality findings, {PROFILE} [{LABEL}]\n\n")
    for name, count in result.data_quality.items():
        sys.stdout.write(
            f"  {name:<28} {count:>3}  (injected {INJECTED[name]})\n      -> {FIXES[name]}\n"
        )
    sys.stdout.write(
        f"\nClean, booked order lines used for insights: {result.clean_order_lines}.\n"
        "Corrections are proposals: a data steward approves them, and a Fabric notebook or pipeline\n"
        "applies them in Silver. The semantic model then refreshes. The Fabric data agent itself is\n"
        "read-only and never changes data.\n"
    )
    return 0


def _cmd_brief(args: argparse.Namespace) -> int:
    settings = Settings()
    profile = MFG_PROFILES[PROFILE]
    result = build(settings.data_root / "raw" / PROFILE, profile)
    teams = [t for t in TEAMS if args.team in (None, t[0])]
    if not teams:
        sys.stderr.write(f"unknown team {args.team!r}; choose from {[t[0] for t in TEAMS]}\n")
        return 2
    if args.json:
        payload = {t[0]: result.team_briefs[t[0]] for t in teams}
        sys.stdout.write(
            json.dumps(
                {
                    "label": "LOCAL",
                    "month": profile.observation_month.isoformat(),
                    "briefs": payload,
                },
                indent=2,
            )
            + "\n"
        )
        return 0
    month = profile.observation_month.strftime("%B %Y")
    for team_id, name, focus_type, focus in teams:
        b = result.team_briefs[team_id]
        sys.stdout.write(
            f"\n=== Monthly brief: {name} ({focus_type.replace('_', ' ')}: {focus.replace('|', ', ')}) - {month}"
            f" [{LABEL}]\n"
            f"  Booked revenue      ${b['revenue']:,.2f}   vs last month {b['mom_change_pct']:+}%"
            f"   vs last year {b['yoy_change_pct']:+}%\n"
            f"  Target attainment   {b['target_attainment_pct']}% of ${b['target']:,.2f}\n"
            f"  Gross margin        {b['gross_margin_pct']}%\n"
            f"  Top growing product {b['top_growing_product']}\n"
            f"  Data-quality issues in scope this month: {b['data_quality_issues_in_month']}\n"
        )
    sys.stdout.write(
        "\nSynthetic demonstration data. In the live demo, a Foundry agent writes this brief from the\n"
        "Fabric data agent's answers and a schedule delivers it to Teams or Outlook.\n"
    )
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``mfg`` subcommands."""
    mfg = subparsers.add_parser("mfg", help="manufacturing workshop data (offline, LOCAL)")
    sub = mfg.add_subparsers(dest="mfg_command", required=True)
    quality = sub.add_parser("quality", help="data-quality findings and proposed corrections")
    quality.add_argument("--json", action="store_true")
    quality.set_defaults(func=_cmd_quality)
    brief = sub.add_parser("brief", help="monthly brief for each business team")
    brief.add_argument("--team", help="team id, for example T-ENC")
    brief.add_argument("--json", action="store_true")
    brief.set_defaults(func=_cmd_brief)
