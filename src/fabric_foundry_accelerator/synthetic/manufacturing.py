"""Synthetic manufacturing sales dataset (``mfg-sales-v1``) for the Foundry + Fabric agent workshop.

A fictional manufacturer ("Fabrikam Industrial") sells five product lines through four regions.
Business teams own focus areas (product lines or a customer segment) and receive a monthly brief.
The generator is deterministic and injects a known number of data-quality issues, so detection,
correction proposals and insights can be checked against a committed baseline:

- duplicate order lines;
- order lines whose product is missing from the product master (a relationship violation);
- shipped lines with a negative quantity;
- unit prices entered per box instead of per each (100x);
- customers with a missing region, and customers with non-standard region labels;
- order dates after the observation cutoff;
- shipped lines without a ship date, and lines shipped before they were ordered.

Synthetic data only. Company, customer and product names are fictional.
"""

import csv
import hashlib
import json
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import duckdb
from pydantic import BaseModel, ConfigDict

GENERATOR_VERSION = "1"
NOTICE = (
    "SYNTHETIC DATA. Fictional manufacturer, customers, products and people generated for "
    "education. Not real sales data."
)


@dataclass(frozen=True, slots=True)
class MfgProfile:
    """A manufacturing dataset profile."""

    id: str
    description: str
    seed: int
    customers: int
    products_per_line: int
    window_start: date
    observation_month: date  # first day of the month the monthly brief covers


MFG_PROFILES: dict[str, MfgProfile] = {
    "mfg-sales-v1": MfgProfile(
        id="mfg-sales-v1",
        description="Fictional manufacturer sales orders with injected data-quality issues",
        seed=20261008,
        customers=140,
        products_per_line=12,
        window_start=date(2025, 1, 1),
        observation_month=date(2026, 9, 1),
    )
}

PRODUCT_LINES: tuple[tuple[str, str, float, float], ...] = (
    # code, name, base list price, margin
    ("STR", "Structural Products", 420.0, 0.31),
    ("MET", "Metal Components", 95.0, 0.27),
    ("ENC", "Enclosures", 260.0, 0.35),
    ("FAS", "Fasteners & Hardware", 18.0, 0.42),
    ("FAB", "Custom Fabrication", 1350.0, 0.24),
)
REGIONS: tuple[str, ...] = ("North America East", "North America West", "Central", "International")
REGION_VARIANTS: tuple[tuple[str, str], ...] = (
    ("North America East", "N. America East"),
    ("North America East", "NA-East"),
    ("North America West", "NA West"),
    ("Central", "CENTRAL "),
    ("International", "Intl"),
    ("North America West", "north america west"),
)
SEGMENTS: tuple[str, ...] = ("Distributor", "OEM", "Contractor", "Key Account")
PLANTS: tuple[tuple[str, str, str], ...] = (
    ("PL-01", "Plant 01 (Midwest)", "Central"),
    ("PL-02", "Plant 02 (Northeast)", "North America East"),
    ("PL-03", "Plant 03 (West)", "North America West"),
    ("PL-04", "Plant 04 (Export)", "International"),
)
TEAMS: tuple[tuple[str, str, str, str], ...] = (
    # team id, name, focus type, focus values (|-separated)
    ("T-STRMET", "Structural & Metals", "product_line", "STR|MET"),
    ("T-ENC", "Enclosures", "product_line", "ENC"),
    ("T-HWFAB", "Hardware & Fabrication", "product_line", "FAS|FAB"),
    ("T-KEY", "Key Accounts", "segment", "Key Account"),
)
_NAME_A = (
    "Summit",
    "Granite",
    "Harbor",
    "Prairie",
    "Cedar",
    "Atlas",
    "Beacon",
    "Ironwood",
    "Lakeside",
    "Pioneer",
    "Redline",
    "Silverleaf",
    "Tri-County",
    "Westfield",
    "Northgate",
    "Riverbend",
)
_NAME_B = (
    "Supply",
    "Builders",
    "Industrial",
    "Fabricators",
    "Distribution",
    "Contractors",
    "Systems",
    "Works",
    "Partners",
    "Equipment",
)
_PRODUCT_WORDS = {
    "STR": ("Beam", "Column", "Truss", "Brace", "Frame", "Purlin"),
    "MET": ("Bracket", "Plate", "Channel", "Angle", "Clip", "Bar"),
    "ENC": ("Cabinet", "Housing", "Panel Box", "Junction Box", "Rack", "Shroud"),
    "FAS": ("Anchor", "Bolt Kit", "Screw Pack", "Rivet Pack", "Washer Set", "Hinge"),
    "FAB": ("Weldment", "Assembly", "Skid", "Platform", "Guard", "Stand"),
}

# How many issues of each kind the generator injects (the baseline must detect exactly these).
INJECTED: dict[str, int] = {
    "duplicate_order_lines": 12,
    "orphan_product_ids": 9,
    "negative_quantity_shipped": 7,
    "unit_price_outliers": 5,
    "missing_customer_region": 4,
    "nonstandard_region_labels": 6,
    "future_order_dates": 3,
    "shipped_without_ship_date": 8,
    "ship_before_order": 4,
}

TABLES = ("plants", "business_teams", "products", "customers", "sales_orders", "sales_targets")


class MfgBaseline(BaseModel):
    """Expected results for a manufacturing profile."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile: str
    generator_version: str
    synthetic_notice: str
    observation_month: str
    row_counts: dict[str, int]
    data_quality: dict[str, int]
    clean_order_lines: int
    observation_month_revenue: float
    team_briefs: dict[str, dict[str, float | int | str | None]]


def _months(start: date, end: date) -> list[date]:
    months: list[date] = []
    current = start
    while current <= end:
        months.append(current)
        current = date(current.year + (current.month == 12), current.month % 12 + 1, 1)
    return months


def generate(profile: MfgProfile) -> dict[str, list[dict[str, str]]]:
    """Generate all tables as rows of strings (CSV-ready)."""
    rng = random.Random(profile.seed)
    cutoff = date(
        profile.observation_month.year + (profile.observation_month.month == 12),
        profile.observation_month.month % 12 + 1,
        1,
    ) - timedelta(days=1)

    plants = [{"plant_id": p, "plant_name": n, "region": r} for p, n, r in PLANTS]
    teams = [
        {
            "team_id": t,
            "team_name": n,
            "focus_type": ft,
            "focus_values": fv,
            "brief_recipient": f"{t.lower()}-leads@example.com",
        }
        for t, n, ft, fv in TEAMS
    ]
    products: list[dict[str, str]] = []
    for code, line_name, base, margin in PRODUCT_LINES:
        for i in range(1, profile.products_per_line + 1):
            word = _PRODUCT_WORDS[code][(i - 1) % len(_PRODUCT_WORDS[code])]
            price = round(base * rng.uniform(0.6, 1.6), 2)
            products.append(
                {
                    "product_id": f"P-{code}-{i:03d}",
                    "product_name": f"{word} {code}-{i:03d}",
                    "product_line": code,
                    "product_line_name": line_name,
                    "unit_of_measure": "EA",
                    "list_price": f"{price:.2f}",
                    "standard_cost": f"{price * (1 - margin) * rng.uniform(0.95, 1.05):.2f}",
                }
            )
    customers: list[dict[str, str]] = []
    for i in range(1, profile.customers + 1):
        segment = rng.choices(SEGMENTS, weights=(40, 25, 25, 10))[0]
        customers.append(
            {
                "customer_id": f"C-{i:04d}",
                "customer_name": f"{rng.choice(_NAME_A)} {rng.choice(_NAME_B)} {i:03d}",
                "segment": segment,
                "region": rng.choices(REGIONS, weights=(32, 26, 28, 14))[0],
                "country": "US",
            }
        )
    for c in customers:
        if c["region"] == "International":
            c["country"] = rng.choice(("CA", "MX", "DE", "AU"))
    # Data-quality: missing and non-standard region labels on distinct customers.
    picks = rng.sample(
        range(len(customers)), INJECTED["missing_customer_region"] + len(REGION_VARIANTS)
    )
    for idx in picks[: INJECTED["missing_customer_region"]]:
        customers[idx]["region"] = ""
    for idx, (canonical, variant) in zip(
        picks[INJECTED["missing_customer_region"] :], REGION_VARIANTS, strict=True
    ):
        customers[idx]["region"] = variant
        customers[idx]["country"] = "US" if canonical != "International" else "CA"

    line_weight = {"STR": 1.0, "MET": 1.6, "ENC": 1.1, "FAS": 2.2, "FAB": 0.45}
    line_growth = {"STR": 0.012, "MET": 0.004, "ENC": 0.021, "FAS": -0.006, "FAB": 0.015}
    months = _months(profile.window_start, profile.observation_month)
    orders: list[dict[str, str]] = []
    order_no = 100000
    for m_index, month in enumerate(months):
        season = 1.0 + 0.18 * (month.month in (4, 5, 6, 9, 10)) - 0.15 * (month.month in (12, 1))
        n_orders = int(rng.gauss(150, 12) * season)
        if month == profile.observation_month:
            n_orders = int(
                n_orders * 0.93
            )  # a softer observation month gives the brief something to explain
        days_in_month = (_months(month, month)[0].replace(day=28) + timedelta(days=4)).replace(
            day=1
        ) - month
        for _ in range(n_orders):
            order_no += 1
            customer = rng.choice(customers)
            order_date = month + timedelta(days=rng.randrange(days_in_month.days))
            for line_number in range(1, rng.choice((1, 1, 1, 2, 2, 3)) + 1):
                code = rng.choices(list(line_weight), weights=list(line_weight.values()))[0]
                if customer["segment"] == "Key Account" and rng.random() < 0.35:
                    code = "FAB"
                trend = (1 + line_growth[code]) ** m_index
                product = rng.choice([p for p in products if p["product_line"] == code])
                qty = max(1, int(rng.lognormvariate(2.2 if code == "FAS" else 1.3, 0.6) * trend))
                if code == "ENC" and month == profile.observation_month:
                    qty = max(1, int(qty * 1.25))  # enclosures surge in the observation month
                discount = rng.choice((0, 0, 0, 2, 5, 5, 8, 10)) + (
                    5 if customer["segment"] == "Key Account" else 0
                )
                price = float(product["list_price"]) * rng.uniform(0.97, 1.03)
                status = "Shipped"
                if month == profile.observation_month and rng.random() < 0.25:
                    status = "Open"
                elif rng.random() < 0.03:
                    status = "Cancelled"
                ship_date = (
                    order_date + timedelta(days=rng.randint(2, 21)) if status == "Shipped" else None
                )
                orders.append(
                    {
                        "order_id": f"SO-{order_no}",
                        "line_number": str(line_number),
                        "order_date": order_date.isoformat(),
                        "ship_date": ship_date.isoformat()
                        if ship_date and ship_date <= cutoff
                        else "",
                        "customer_id": customer["customer_id"],
                        "product_id": product["product_id"],
                        "plant_id": rng.choice([p[0] for p in PLANTS]),
                        "quantity": str(qty),
                        "unit_price": f"{price:.2f}",
                        "discount_pct": str(discount),
                        "currency": "USD",
                        "status": status if (ship_date is None or ship_date <= cutoff) else "Open",
                    }
                )
    # Lines shipped after the cutoff became "Open" above; keep their ship date empty.
    _inject_order_issues(rng, orders, cutoff)

    targets: list[dict[str, str]] = []
    for month in months:
        for team_id, *_ in TEAMS:
            base = {"T-STRMET": 98000, "T-ENC": 52000, "T-HWFAB": 225000, "T-KEY": 52000}[team_id]
            growth = (1.01) ** months.index(month)
            targets.append(
                {
                    "month": month.isoformat(),
                    "team_id": team_id,
                    "target_revenue": f"{base * growth * rng.uniform(0.97, 1.03):.2f}",
                }
            )
    return {
        "plants": plants,
        "business_teams": teams,
        "products": products,
        "customers": customers,
        "sales_orders": orders,
        "sales_targets": targets,
    }


def _inject_order_issues(rng: random.Random, orders: list[dict[str, str]], cutoff: date) -> None:
    shipped = [i for i, o in enumerate(orders) if o["status"] == "Shipped" and o["ship_date"]]
    needed = sum(
        INJECTED[k]
        for k in (
            "orphan_product_ids",
            "negative_quantity_shipped",
            "unit_price_outliers",
            "shipped_without_ship_date",
            "ship_before_order",
        )
    )
    chosen = rng.sample(shipped, needed)
    cursor = 0

    def take(kind: str) -> list[int]:
        nonlocal cursor
        picked = chosen[cursor : cursor + INJECTED[kind]]
        cursor += INJECTED[kind]
        return picked

    for n, idx in enumerate(take("orphan_product_ids")):
        orders[idx]["product_id"] = f"P-RET-{900 + n:03d}"  # retired codes missing from the master
    for idx in take("negative_quantity_shipped"):
        orders[idx]["quantity"] = str(-abs(int(orders[idx]["quantity"])))
    for idx in take("unit_price_outliers"):
        orders[idx]["unit_price"] = f"{float(orders[idx]['unit_price']) * 100:.2f}"
    for idx in take("shipped_without_ship_date"):
        orders[idx]["ship_date"] = ""
    for idx in take("ship_before_order"):
        order_day = date.fromisoformat(orders[idx]["order_date"])
        orders[idx]["ship_date"] = (order_day - timedelta(days=rng.randint(1, 5))).isoformat()
    for n in range(INJECTED["future_order_dates"]):
        template = dict(rng.choice(orders))
        template["order_id"] = f"SO-9{n:05d}"
        template["order_date"] = (cutoff + timedelta(days=rng.randint(10, 60))).isoformat()
        template["ship_date"] = ""
        template["status"] = "Open"
        orders.append(template)
    for idx in rng.sample(
        range(len(orders) - INJECTED["future_order_dates"]), INJECTED["duplicate_order_lines"]
    ):
        orders.append(dict(orders[idx]))
    orders.sort(key=lambda o: (o["order_date"], o["order_id"], o["line_number"]))


def write_csvs(tables: dict[str, list[dict[str, str]]], out_dir: Path) -> dict[str, str]:
    """Write one CSV per table; return {file: sha256}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    digests: dict[str, str] = {}
    for name in TABLES:
        rows = tables[name]
        path = out_dir / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        digests[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


# --------------------------------------------------------------------------- local build (DuckDB)
_SILVER_ORDERS = """
CREATE TABLE silver_sales_orders AS
WITH typed AS (
    SELECT
        o.order_id, CAST(o.line_number AS INTEGER) AS line_number,
        TRY_CAST(o.order_date AS DATE) AS order_date, TRY_CAST(NULLIF(o.ship_date, '') AS DATE) AS ship_date,
        o.customer_id, o.product_id, o.plant_id,
        CAST(o.quantity AS INTEGER) AS quantity, CAST(o.unit_price AS DECIMAL(12, 2)) AS unit_price,
        CAST(o.discount_pct AS INTEGER) AS discount_pct, o.status,
        row_number() OVER (PARTITION BY o.order_id, o.line_number ORDER BY o.order_id) AS copy_number
    FROM bronze_sales_orders AS o
)
SELECT
    t.*,
    p.product_line, p.list_price, p.standard_cost,
    t.copy_number > 1 AS is_duplicate,
    p.product_id IS NULL AS is_orphan_product,
    t.quantity < 0 AND t.status = 'Shipped' AS is_negative_shipped,
    p.list_price IS NOT NULL AND t.unit_price > 20 * p.list_price AS is_price_outlier,
    t.order_date > DATE '{cutoff}' AS is_future_order,
    t.status = 'Shipped' AND t.ship_date IS NULL AS is_shipped_without_date,
    t.ship_date IS NOT NULL AND t.ship_date < t.order_date AS is_ship_before_order
FROM typed AS t
LEFT JOIN silver_products AS p USING (product_id)
"""

_REGION_MAP = {
    **{r: r for r in REGIONS},
    **{v.strip().lower(): c for c, v in REGION_VARIANTS},
    **{r.lower(): r for r in REGIONS},
}


@dataclass(frozen=True, slots=True)
class MfgBuild:
    """The local build: data-quality counts, clean line count and per-team briefs."""

    data_quality: dict[str, int]
    clean_order_lines: int
    observation_month_revenue: float
    team_briefs: dict[str, dict[str, float | int | str | None]]


def observation_cutoff(profile: MfgProfile) -> date:
    """Last day of the observation month."""
    month = profile.observation_month
    return date(month.year + (month.month == 12), month.month % 12 + 1, 1) - timedelta(days=1)


def open_sales(
    raw_dir: Path, profile: MfgProfile
) -> tuple[duckdb.DuckDBPyConnection, dict[str, int]]:
    """Build Bronze, Silver (with data-quality flags) and ``gold_sales`` in memory.

    Returns the open connection (the caller closes it) and the data-quality counts.
    """
    cutoff = observation_cutoff(profile).isoformat()
    con = duckdb.connect()
    try:
        for name in TABLES:
            con.execute(
                f"CREATE TABLE bronze_{name} AS SELECT * FROM read_csv(?, header = true, all_varchar = true)",
                [str(raw_dir / f"{name}.csv")],
            )
        con.execute(
            "CREATE TABLE silver_products AS SELECT product_id, product_line, "
            "CAST(list_price AS DECIMAL(12, 2)) AS list_price, "
            "CAST(standard_cost AS DECIMAL(12, 2)) AS standard_cost FROM bronze_products"
        )
        con.execute("CREATE TABLE region_map (label VARCHAR, region VARCHAR)")
        con.executemany("INSERT INTO region_map VALUES (?, ?)", list(_REGION_MAP.items()))
        con.execute(
            "CREATE TABLE silver_customers AS SELECT c.customer_id, c.segment, c.region AS region_raw, "
            "COALESCE(m.region, 'Unmapped') AS region, NULLIF(TRIM(c.region), '') IS NULL AS is_missing_region, "
            "NULLIF(TRIM(c.region), '') IS NOT NULL AND c.region NOT IN "
            f"({', '.join(repr(r) for r in REGIONS)}) AS is_nonstandard_region "
            "FROM bronze_customers AS c LEFT JOIN region_map AS m ON lower(trim(c.region)) = m.label"
        )
        con.execute(_SILVER_ORDERS.format(cutoff=cutoff))
        flags = {
            "duplicate_order_lines": "is_duplicate",
            "orphan_product_ids": "is_orphan_product",
            "negative_quantity_shipped": "is_negative_shipped",
            "unit_price_outliers": "is_price_outlier",
            "future_order_dates": "is_future_order",
            "shipped_without_ship_date": "is_shipped_without_date",
            "ship_before_order": "is_ship_before_order",
        }
        quality: dict[str, int] = {}
        for name, column in flags.items():
            row = con.execute(f"SELECT count(*) FROM silver_sales_orders WHERE {column}").fetchone()
            quality[name] = int(row[0]) if row else 0
        for name, column in (
            ("missing_customer_region", "is_missing_region"),
            ("nonstandard_region_labels", "is_nonstandard_region"),
        ):
            row = con.execute(f"SELECT count(*) FROM silver_customers WHERE {column}").fetchone()
            quality[name] = int(row[0]) if row else 0
        any_flag = " OR ".join(flags.values())
        con.execute(
            "CREATE TABLE gold_sales AS SELECT o.*, c.segment, c.region, "
            "o.quantity * o.unit_price * (1 - o.discount_pct / 100.0) AS revenue, "
            "o.quantity * (o.unit_price * (1 - o.discount_pct / 100.0) - o.standard_cost) AS margin "
            f"FROM silver_sales_orders AS o JOIN silver_customers AS c USING (customer_id) WHERE NOT ({any_flag}) "
            "AND o.status <> 'Cancelled'"
        )
    except BaseException:
        con.close()
        raise
    return con, quality


def line_revenue(con: duckdb.DuckDBPyConnection, month: date) -> dict[str, float]:
    """Booked revenue by product line for one month, from ``gold_sales``."""
    rows = con.execute(
        "SELECT product_line, round(sum(revenue), 2) FROM gold_sales "
        "WHERE date_trunc('month', order_date) = ? GROUP BY product_line ORDER BY product_line",
        [month],
    ).fetchall()
    return {str(line): float(total) for line, total in rows}


def build(raw_dir: Path, profile: MfgProfile) -> MfgBuild:
    """Load raw CSVs, build typed Silver with data-quality flags, and compute the monthly briefs."""
    month = profile.observation_month
    con, quality = open_sales(raw_dir, profile)
    with con:
        clean = con.execute("SELECT count(*) FROM gold_sales").fetchone()
        month_revenue = con.execute(
            "SELECT round(sum(revenue), 2) FROM gold_sales WHERE date_trunc('month', order_date) = ?",
            [month],
        ).fetchone()
        briefs = {
            team[0]: _brief(con, team, month, quality_scope=_team_issue_count(con, team, month))
            for team in TEAMS
        }
    return MfgBuild(
        data_quality=quality,
        clean_order_lines=int(clean[0]) if clean else 0,
        observation_month_revenue=float(month_revenue[0])
        if month_revenue and month_revenue[0] is not None
        else 0.0,
        team_briefs=briefs,
    )


def _team_filter(team: tuple[str, str, str, str], alias: str = "") -> str:
    _, _, focus_type, values = team
    column = "product_line" if focus_type == "product_line" else "segment"
    items = ", ".join(repr(v) for v in values.split("|"))
    return f"{alias}{column} IN ({items})"


def _team_issue_count(
    con: duckdb.DuckDBPyConnection, team: tuple[str, str, str, str], month: date
) -> int:
    flags = (
        "is_duplicate",
        "is_orphan_product",
        "is_negative_shipped",
        "is_price_outlier",
        "is_shipped_without_date",
        "is_ship_before_order",
    )
    where = " OR ".join(flags)
    scope = _team_filter(team, "o." if team[2] == "product_line" else "c.")
    # Orphan products have no product line; count them for product-line teams only via the raw code prefix.
    row = con.execute(
        "SELECT count(*) FROM silver_sales_orders AS o JOIN silver_customers AS c USING (customer_id) "
        f"WHERE date_trunc('month', o.order_date) = ? AND ({where}) AND ({scope} OR o.is_orphan_product)",
        [month],
    ).fetchone()
    return int(row[0]) if row else 0


def _brief(
    con: duckdb.DuckDBPyConnection,
    team: tuple[str, str, str, str],
    month: date,
    *,
    quality_scope: int,
) -> dict[str, float | int | str | None]:
    prev = date(month.year - (month.month == 1), (month.month - 2) % 12 + 1, 1)
    last_year = date(month.year - 1, month.month, 1)
    where = _team_filter(team)

    def revenue(m: date) -> float:
        row = con.execute(
            f"SELECT coalesce(sum(revenue), 0) FROM gold_sales WHERE {where} AND date_trunc('month', order_date) = ?",
            [m],
        ).fetchone()
        return float(row[0]) if row else 0.0

    current, previous, prior_year = revenue(month), revenue(prev), revenue(last_year)
    target_row = con.execute(
        "SELECT CAST(target_revenue AS DOUBLE) FROM bronze_sales_targets WHERE team_id = ? AND month = ?",
        [team[0], month.isoformat()],
    ).fetchone()
    target = float(target_row[0]) if target_row else 0.0
    margin_row = con.execute(
        "SELECT sum(margin) / nullif(sum(revenue), 0) FROM gold_sales "
        f"WHERE {where} AND date_trunc('month', order_date) = ?",
        [month],
    ).fetchone()
    mover = con.execute(
        f"SELECT product_id, sum(CASE WHEN date_trunc('month', order_date) = ? THEN revenue ELSE 0 END) "
        f"- sum(CASE WHEN date_trunc('month', order_date) = ? THEN revenue ELSE 0 END) AS delta "
        f"FROM gold_sales WHERE {where} GROUP BY product_id ORDER BY delta DESC, product_id LIMIT 1",
        [month, prev],
    ).fetchone()
    return {
        "team_name": team[1],
        "revenue": round(current, 2),
        "revenue_previous_month": round(previous, 2),
        "revenue_same_month_last_year": round(prior_year, 2),
        "mom_change_pct": round(100 * (current - previous) / previous, 1) if previous else None,
        "yoy_change_pct": round(100 * (current - prior_year) / prior_year, 1)
        if prior_year
        else None,
        "target": round(target, 2),
        "target_attainment_pct": round(100 * current / target, 1) if target else None,
        "gross_margin_pct": round(100 * float(margin_row[0]), 1)
        if margin_row and margin_row[0] is not None
        else None,
        "top_growing_product": str(mover[0]) if mover else None,
        "data_quality_issues_in_month": quality_scope,
    }


def baseline(profile: MfgProfile, raw_dir: Path) -> MfgBaseline:
    """Compute the committed baseline from the raw CSVs."""
    result = build(raw_dir, profile)
    counts: dict[str, int] = {}
    for name in TABLES:
        with (raw_dir / f"{name}.csv").open(encoding="utf-8") as handle:
            counts[name] = sum(1 for _ in csv.DictReader(handle))
    return MfgBaseline(
        profile=profile.id,
        generator_version=GENERATOR_VERSION,
        synthetic_notice=NOTICE,
        observation_month=profile.observation_month.isoformat(),
        row_counts=counts,
        data_quality=result.data_quality,
        clean_order_lines=result.clean_order_lines,
        observation_month_revenue=result.observation_month_revenue,
        team_briefs=result.team_briefs,
    )


def write_profile(profile: MfgProfile, data_root: Path) -> MfgBaseline:
    """Generate CSVs, manifest and baseline under ``data_root``."""
    raw_dir = data_root / "raw" / profile.id
    digests = write_csvs(generate(profile), raw_dir)
    manifest = {
        "profile": profile.id,
        "generator_version": GENERATOR_VERSION,
        "synthetic_notice": NOTICE,
        "observation_month": profile.observation_month.isoformat(),
        "injected_quality_issues": INJECTED,
        "files": digests,
    }
    (raw_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (raw_dir / "SHA256SUMS").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(digests.items())), encoding="utf-8"
    )
    result = baseline(profile, raw_dir)
    expected = data_root / "expected" / f"{profile.id}.json"
    expected.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return result
