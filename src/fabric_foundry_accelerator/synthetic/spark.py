"""Fabric Spark reference notebooks generated from the packaged medallion SQL.

The local build runs the SQL on DuckDB. The same SQL becomes Fabric PySpark notebooks through a
closed set of dialect rewrites. Any DuckDB-only construct not in that set fails generation instead
of producing a notebook that might fail on Fabric Spark.

Notebooks use the Fabric Git source format (``notebook-content.py`` plus ``.platform``). They are
reviewed definitions: the scoped writer creates a notebook item only from these files. No workspace
or lakehouse ID is committed; attach the default lakehouse when you open the notebook.
"""

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fabric_foundry_accelerator.models.semantic import SemanticModel
from fabric_foundry_accelerator.synthetic.baseline import FACT_TABLES, Baseline
from fabric_foundry_accelerator.synthetic.medallion import (
    DIAGNOSTICS,
    GOLD_SPECS,
    ROW_PRESERVATION,
    SILVER_MASTER_SPECS,
    SILVER_SPECS,
    TableSpec,
    read_sql,
)
from fabric_foundry_accelerator.synthetic.profiles import DatasetProfile

READMISSION_TABLES = {"hc_lab": "gold_readmissions", "core_star": "gold_readmission_demo"}


class SparkDialectError(ValueError):
    """Raised when SQL uses a DuckDB construct outside the supported rewrite set."""


_FORMAT_TOKENS = {"%Y": "yyyy", "%m": "MM", "%d": "dd", "%H": "HH", "%M": "mm", "%S": "ss"}
_ARG = r"(`?[A-Za-z_][\w.]*`?)"


def _spark_format(duckdb_format: str) -> str:
    result = duckdb_format
    for token, spark in _FORMAT_TOKENS.items():
        result = result.replace(token, spark)
    if "%" in result:
        raise SparkDialectError(f"unsupported strptime/strftime format {duckdb_format!r}")
    return result


Rewrite = tuple[re.Pattern[str], Callable[[re.Match[str]], str]]

REWRITES: tuple[Rewrite, ...] = (
    # DuckDB quotes identifiers with double quotes; Spark SQL uses backticks. Runs first so the
    # function rewrites below also match quoted arguments.
    (re.compile(r'"([A-Za-z_][A-Za-z0-9_]*)"'), lambda m: f"`{m[1]}`"),
    (
        re.compile(
            r"CAST\(\s*unnest\(\s*generate_series\(\s*CAST\("
            + _ARG
            + r" AS TIMESTAMP\),\s*CAST\("
            + _ARG
            + r" AS TIMESTAMP\),\s*INTERVAL 1 DAY\s*\)\s*\)\s*AS DATE\s*\)",
            re.IGNORECASE,
        ),
        lambda m: f"explode(sequence(CAST({m[1]} AS DATE), CAST({m[2]} AS DATE), INTERVAL 1 DAY))",
    ),
    (
        re.compile(r"\btry_strptime\(\s*" + _ARG + r",\s*'([^']*)'\s*\)", re.IGNORECASE),
        lambda m: f"try_to_timestamp({m[1]}, '{_spark_format(m[2])}')",
    ),
    (
        re.compile(r"\bstrftime\(\s*" + _ARG + r",\s*'([^']*)'\s*\)", re.IGNORECASE),
        lambda m: f"date_format({m[1]}, '{_spark_format(m[2])}')",
    ),
    (
        re.compile(r"\bdate_diff\(\s*'day',\s*" + _ARG + r",\s*" + _ARG + r"\s*\)", re.IGNORECASE),
        lambda m: f"datediff({m[2]}, {m[1]})",
    ),
    (
        re.compile(r"\bisodow\(\s*" + _ARG + r"\s*\)", re.IGNORECASE),
        lambda m: f"((dayofweek({m[1]}) + 5) % 7 + 1)",
    ),
    (
        re.compile(r"\bmonthname\(\s*" + _ARG + r"\s*\)", re.IGNORECASE),
        lambda m: f"date_format({m[1]}, 'MMMM')",
    ),
    (
        re.compile(r"\bdayname\(\s*" + _ARG + r"\s*\)", re.IGNORECASE),
        lambda m: f"date_format({m[1]}, 'EEEE')",
    ),
    (re.compile(r"\bstarts_with\(", re.IGNORECASE), lambda _: "startswith("),
    (re.compile(r"\bstrpos\(", re.IGNORECASE), lambda _: "instr("),
    # Spark requires a length for VARCHAR; an unbounded DuckDB VARCHAR is a Spark STRING.
    (re.compile(r"\bVARCHAR\b(?!\s*\()", re.IGNORECASE), lambda _: "STRING"),
)
DUCKDB_ONLY = re.compile(
    r"\b(try_strptime|strftime|strptime|date_diff|isodow|monthname|dayname|starts_with|strpos|"
    r"generate_series|unnest|read_csv|read_parquet|list_\w+|epoch)\s*\(|::|\bQUALIFY\b|\bEXCLUDE\b|"
    r"\b(TIMESTAMPTZ|HUGEINT|UBIGINT|UINTEGER)\b",
    re.IGNORECASE,
)


_COMMENT = re.compile(r"--[^\n]*")


def to_spark_sql(duckdb_sql: str) -> str:
    """Rewrite one DuckDB SELECT into Spark SQL, or raise ``SparkDialectError``."""
    sql = duckdb_sql
    for pattern, replace in REWRITES:
        sql = pattern.sub(replace, sql)
    code = _COMMENT.sub("", sql)  # prose in comments is not SQL
    leftover = DUCKDB_ONLY.search(code)
    if leftover:
        raise SparkDialectError(f"DuckDB-only construct {leftover[0]!r} has no Spark rewrite")
    if '"' in code:
        raise SparkDialectError("double-quoted text remains; Spark reads it as a string literal")
    return sql.strip()


CellKind = Literal["markdown", "parameters", "code"]


@dataclass(frozen=True, slots=True)
class Cell:
    """One notebook cell."""

    kind: CellKind
    source: str


_RULE = "*" * 20
_KERNEL_META = {"kernel_info": {"name": "synapse_pyspark"}, "dependencies": {}}
_CELL_META = {"language": "python", "language_group": "synapse_pyspark"}


def _meta_block(meta: Mapping[str, object]) -> list[str]:
    body = json.dumps(meta, indent=2).splitlines()
    return [f"# METADATA {_RULE}", "", *(f"# META {line}" for line in body)]


def render_notebook_content(cells: list[Cell]) -> str:
    """Render cells in the Fabric Git source format for a PySpark notebook."""
    lines = ["# Fabric notebook source", "", *_meta_block(_KERNEL_META)]
    for cell in cells:
        lines.append("")
        if cell.kind == "markdown":
            lines += [f"# MARKDOWN {_RULE}", ""]
            lines += [f"# {line}".rstrip() for line in cell.source.strip().splitlines()]
            continue
        marker = "PARAMETERS CELL" if cell.kind == "parameters" else "CELL"
        lines += [f"# {marker} {_RULE}", "", *cell.source.strip().splitlines(), ""]
        lines += _meta_block(_CELL_META)
    return "\n".join(lines) + "\n"


PLATFORM_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json"


def render_platform(display_name: str, description: str, logical_id: str) -> str:
    """Render the ``.platform`` file. ``logical_id`` is a synthetic, committed placeholder."""
    platform = {
        "$schema": PLATFORM_SCHEMA,
        "metadata": {"type": "Notebook", "displayName": display_name, "description": description},
        "config": {"version": "2.0", "logicalId": logical_id},
    }
    return json.dumps(platform, indent=2) + "\n"


# --------------------------------------------------------------------------- notebook content
_HELPERS = '''
from pyspark.sql import functions as F

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str) -> None:
    """Record and print one validation result."""
    CHECKS.append((name, passed, detail))
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")


def write_table(df, name: str) -> int:
    """Overwrite one table and return the persisted (read-back) row count."""
    (
        df.write.format(TABLE_FORMAT)
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(name)
    )
    return spark.table(name).count()


def scalar(sql: str):
    """Return the single value of a one-row, one-column query."""
    return spark.sql(sql).collect()[0][0]


def key_check(table: str, keys: list[str]) -> None:
    """Keys are populated and unique."""
    cols = ", ".join(f"`{k}`" for k in keys)
    populated = " AND ".join(f"`{k}` IS NOT NULL" for k in keys)
    total = scalar(f"SELECT count(*) FROM `{table}`")
    distinct = scalar(f"SELECT count(DISTINCT {cols}) FROM `{table}` WHERE {populated}")
    filled = scalar(f"SELECT count(*) FROM `{table}` WHERE {populated}")
    check(
        f"{table}: key ({', '.join(keys)}) populated and unique",
        total == distinct == filled,
        f"rows {total}, distinct keys {distinct}, populated keys {filled}",
    )


def finish() -> None:
    """Stop the run if any check failed, so a failed layer is never reported as built."""
    failed = [name for name, passed, _ in CHECKS if not passed]
    if failed:
        raise AssertionError(f"{len(failed)} check(s) failed: {failed}")
    print(f"All {len(CHECKS)} checks passed.")
'''.strip()


def _py(value: object) -> str:
    return json.dumps(value, indent=4, sort_keys=True)


def _sql_block(specs: tuple[TableSpec, ...]) -> str:
    lines = ["SQL = {}"]
    for spec in specs:
        sql = to_spark_sql(read_sql(spec.sql_file))
        if '"""' in sql:  # pragma: no cover - guarded by to_spark_sql
            raise SparkDialectError("SQL cannot contain triple quotes")
        lines += [f'SQL["{spec.name}"] = """', sql, '"""', ""]
    return "\n".join(lines).strip()


def _intro(title: str, body: str, profile: DatasetProfile) -> Cell:
    return Cell(
        "markdown",
        f"""
# {title}

**Synthetic data only.** {profile.description}

{body.strip()}

- Attach the default lakehouse (for example `healthcare_lakehouse`) before running. No workspace or
  lakehouse ID is stored in this definition.
- Generated by `ffia notebooks render` from the same SQL the offline build runs on DuckDB. Do not
  hand-edit; change the SQL and re-render.
- A run in the portal or editor is not an MCP job. Evidence is the printed checks and read-back counts.
""",
    )


def bronze_cells(profile: DatasetProfile, expected: Baseline) -> list[Cell]:
    """Cells for the Bronze notebook."""
    raw = {t: expected.row_counts["raw"][t] for t in profile.tables}
    return [
        _intro(
            "MCP_01_Bronze: land the raw CSVs as Bronze Delta tables",
            """
Reads the seven CSVs from `Files/raw` and writes `bronze_` tables with lineage columns.

Design choice to compare in INSPECT: the lab prompt asks for `inferSchema`. This reference reads
every column as **string** so Bronze preserves source values exactly (no silent date or number
coercion). Silver applies explicit, reviewed types. `multiLine` and the double-quote escape keep the
quoted notes intact; the literal `\\n` text and blank condition `encounter_id` values are preserved.
""",
            profile,
        ),
        Cell(
            "parameters",
            f'''
PROFILE = "{profile.id}"
RAW_PATH = "Files/raw"
TABLE_FORMAT = "delta"
EXPECTED_RAW_ROWS = {_py(raw)}
''',
        ),
        Cell("code", _HELPERS),
        Cell(
            "code",
            '''
def read_raw(table: str):
    """Read one CSV as strings, failing on malformed rows instead of dropping them."""
    return (
        spark.read.option("header", True)
        .option("multiLine", True)
        .option("quote", '"')
        .option("escape", '"')
        .option("mode", "FAILFAST")
        .csv(f"{RAW_PATH}/{table}.csv")
    )


for table, expected_rows in EXPECTED_RAW_ROWS.items():
    df = read_raw(table)
    parsed = df.count()
    check(
        f"bronze_{table}: parsed rows equal source baseline",
        parsed == expected_rows,
        f"parsed {parsed}, expected {expected_rows}",
    )
    if parsed != expected_rows:
        continue  # never write a table whose parse does not match the baseline
    lineage = df.withColumn("_source_file", F.lit(f"raw/{PROFILE}/{table}.csv")).withColumn(
        "_ingested_at", F.current_timestamp()
    )
    persisted = write_table(lineage, f"bronze_{table}")
    check(f"bronze_{table}: persisted rows equal parsed rows", persisted == parsed, f"persisted {persisted}")

finish()
''',
        ),
    ]


def silver_cells(profile: DatasetProfile, expected: Baseline) -> list[Cell]:
    """Cells for the Silver notebook."""
    specs = (SILVER_MASTER_SPECS if profile.reference_masters else ()) + SILVER_SPECS
    silver_rows = {s.name: expected.row_counts["silver"][s.name] for s in specs}
    diagnostics = expected.diagnostics
    return [
        _intro(
            "MCP_02_Silver: typed, row-preserving Silver tables",
            """
Applies explicit types, date parsing, bands, condition mapping and data-quality flags. Every Silver
table keeps its Bronze row count. Diagnostics must match the counts the generator injected.
""",
            profile,
        ),
        Cell(
            "parameters",
            f"""
TABLE_FORMAT = "delta"
EXPECTED_SILVER_ROWS = {_py(silver_rows)}
EXPECTED_DIAGNOSTICS = {_py(diagnostics)}
DIAGNOSTICS = {_py({k: list(v) for k, v in DIAGNOSTICS.items()})}
KEYS = {_py({s.name: list(s.keys) for s in specs})}
""",
        ),
        Cell("code", _HELPERS),
        Cell("code", _sql_block(specs)),
        Cell(
            "code",
            """
for name, sql in SQL.items():
    persisted = write_table(spark.sql(sql), name)
    expected_rows = EXPECTED_SILVER_ROWS[name]
    check(f"{name}: rows equal baseline", persisted == expected_rows, f"{persisted} (baseline {expected_rows})")
    key_check(name, KEYS[name])
    bronze = name.replace("silver_", "bronze_", 1)
    if spark.catalog.tableExists(bronze):
        source = spark.table(bronze).count()
        check(f"{name}: row count preserved from {bronze}", persisted == source, f"silver {persisted}, bronze {source}")

for name, (table, predicate) in DIAGNOSTICS.items():
    found = scalar(f"SELECT count(*) FROM `{table}` WHERE {predicate}")
    expected_count = EXPECTED_DIAGNOSTICS[name]
    check(f"diagnostic {name}", found == expected_count, f"found {found}, expected {expected_count}")

finish()
""",
        ),
    ]


def gold_cells(
    profile: DatasetProfile, expected: Baseline, model: SemanticModel | None
) -> list[Cell]:
    """Cells for the Gold notebook."""
    specs = GOLD_SPECS[profile.gold_model]
    gold_rows = {s.name: expected.row_counts["gold"][s.name] for s in specs if not s.staging}
    encounters, claims = FACT_TABLES[profile.gold_model]
    relationships = (
        [[r.to_table, r.to_column, r.from_table, r.from_column] for r in model.relationships]
        if model
        else []
    )
    return [
        _intro(
            "MCP_03_Gold: reviewed grains, dimensions and reconciliation",
            """
Builds the Gold tables and physical dimensions, then checks keys, row preservation, missing
dimension keys and financial reconciliation with Silver. Prints the readmission numerator and
denominator.
""",
            profile,
        ),
        Cell(
            "parameters",
            f'''
TABLE_FORMAT = "delta"
EXPECTED_GOLD_ROWS = {_py(gold_rows)}
EXPECTED_RECONCILIATION = {_py(expected.reconciliation)}
STAGING = {_py([s.name for s in specs if s.staging])}
KEYS = {_py({s.name: list(s.keys) for s in specs if not s.staging})}
ROW_PRESERVATION = {_py([list(p) for p in ROW_PRESERVATION[profile.gold_model]])}
RELATIONSHIPS = {_py(relationships)}
ENCOUNTERS, CLAIMS = "{encounters}", "{claims}"
READMISSIONS = "{READMISSION_TABLES[profile.gold_model]}"
''',
        ),
        Cell("code", _HELPERS),
        Cell("code", _sql_block(specs)),
        Cell(
            "code",
            """
for name, sql in SQL.items():
    if name in STAGING:
        spark.sql(sql).createOrReplaceTempView(name)
        continue
    persisted = write_table(spark.sql(sql), name)
    expected_rows = EXPECTED_GOLD_ROWS[name]
    check(f"{name}: rows equal baseline", persisted == expected_rows, f"{persisted} (baseline {expected_rows})")
    key_check(name, KEYS[name])

for gold, silver in ROW_PRESERVATION:
    g, s = spark.table(gold).count(), spark.table(silver).count()
    check(f"{gold}: row count equals {silver} (no multiplication or loss)", g == s, f"{gold} {g}, {silver} {s}")

for fact, fact_column, dimension, dimension_column in RELATIONSHIPS:
    missing = scalar(
        f"SELECT count(*) FROM `{fact}` AS f LEFT JOIN `{dimension}` AS d "
        f"ON f.`{fact_column}` = d.`{dimension_column}` "
        f"WHERE f.`{fact_column}` IS NOT NULL AND d.`{dimension_column}` IS NULL"
    )
    check(
        f"{fact}.{fact_column} -> {dimension}.{dimension_column}: no missing dimension keys",
        missing == 0,
        f"{missing} missing",
    )
""",
        ),
        Cell(
            "code",
            """
actual = {
    "silver_claim_amount_total": scalar("SELECT sum(claim_amount) FROM silver_claims"),
    "gold_claim_amount_total": scalar(f"SELECT sum(claim_amount) FROM {CLAIMS}"),
    "silver_paid_amount_total": scalar("SELECT sum(paid_amount) FROM silver_claims"),
    "gold_paid_amount_total": scalar(f"SELECT sum(paid_amount) FROM {CLAIMS}"),
    "silver_total_charges": scalar("SELECT sum(total_charges) FROM silver_encounters"),
    "gold_total_charges": scalar(f"SELECT sum(total_charges) FROM {ENCOUNTERS}"),
}
for key, value in actual.items():
    expected_value = EXPECTED_RECONCILIATION[key]
    matches = abs(float(value) - float(expected_value)) < 0.005
    check(f"reconciliation {key}", matches, f"{value} (baseline {expected_value})")

numerator = scalar(f"SELECT count(*) FROM {READMISSIONS} WHERE is_followup_eligible AND is_readmitted_30d")
denominator = scalar(f"SELECT count(*) FROM {READMISSIONS} WHERE is_followup_eligible")
print(f"30-day readmissions (synthetic demonstration): {numerator} of {denominator} eligible index encounters")

finish()
""",
        ),
    ]


@dataclass(frozen=True, slots=True)
class NotebookDefinition:
    """One reviewed notebook definition in Fabric Git format."""

    name: str
    description: str
    logical_id: str
    cells: list[Cell]

    def files(self) -> dict[str, str]:
        """Return relative file names and contents."""
        return {
            "notebook-content.py": render_notebook_content(self.cells),
            ".platform": render_platform(self.name, self.description, self.logical_id),
        }


def hc01_notebooks(
    profile: DatasetProfile, expected: Baseline, model: SemanticModel | None
) -> list[NotebookDefinition]:
    """The three HC-01 reference notebooks (names match the guide's rehearsal items)."""
    return [
        NotebookDefinition(
            "MCP_01_Bronze",
            "HC-01 reference: land raw CSVs as Bronze Delta tables (synthetic data).",
            "00000000-0000-0000-0000-000000000101",
            bronze_cells(profile, expected),
        ),
        NotebookDefinition(
            "MCP_02_Silver",
            "HC-01 reference: typed, row-preserving Silver tables (synthetic data).",
            "00000000-0000-0000-0000-000000000102",
            silver_cells(profile, expected),
        ),
        NotebookDefinition(
            "MCP_03_Gold",
            "HC-01 reference: Gold grains, dimensions and reconciliation (synthetic data).",
            "00000000-0000-0000-0000-000000000103",
            gold_cells(profile, expected, model),
        ),
    ]


def notebook_dir(definitions_root: Path, name: str) -> Path:
    """Return the Git-format folder for a notebook."""
    return definitions_root / f"{name}.Notebook"


def stale_or_missing(definitions_root: Path, notebooks: list[NotebookDefinition]) -> list[Path]:
    """Return files that differ from the rendered definitions."""
    stale: list[Path] = []
    for notebook in notebooks:
        for name, content in notebook.files().items():
            path = notebook_dir(definitions_root, notebook.name) / name
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
    return stale


def write_notebooks(definitions_root: Path, notebooks: list[NotebookDefinition]) -> list[Path]:
    """Write every definition; return the written paths."""
    written: list[Path] = []
    for notebook in notebooks:
        folder = notebook_dir(definitions_root, notebook.name)
        folder.mkdir(parents=True, exist_ok=True)
        for name, content in notebook.files().items():
            path = folder / name
            path.write_text(content, encoding="utf-8")
            written.append(path)
    return written
