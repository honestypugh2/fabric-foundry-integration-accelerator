"""Fabric reference notebooks: DuckDB→Spark rewrites, Git-format rendering and staleness checks."""

import json
from pathlib import Path

import pytest
from tests.conftest import REPO_ROOT

from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.synthetic.medallion import (
    GOLD_SPECS,
    SILVER_MASTER_SPECS,
    SILVER_SPECS,
    read_sql,
)
from fabric_foundry_accelerator.synthetic.notebook_commands import reference_notebooks
from fabric_foundry_accelerator.synthetic.spark import (
    PLATFORM_SCHEMA,
    Cell,
    SparkDialectError,
    render_notebook_content,
    stale_or_missing,
    to_spark_sql,
    write_notebooks,
)

DATA_ROOT = REPO_ROOT / "data" / "synthetic"


@pytest.mark.parametrize(
    ("duckdb", "spark"),
    [
        ("try_strptime(d, '%Y-%m-%d')", "try_to_timestamp(d, 'yyyy-MM-dd')"),
        (
            "try_strptime(\"timestamp\", '%Y-%m-%d %H:%M:%S')",
            "try_to_timestamp(`timestamp`, 'yyyy-MM-dd HH:mm:ss')",
        ),
        ("strftime(d, '%Y-%m')", "date_format(d, 'yyyy-MM')"),
        ("date_diff('day', a.x, b.y)", "datediff(b.y, a.x)"),
        ("isodow(d)", "((dayofweek(d) + 5) % 7 + 1)"),
        ("monthname(d)", "date_format(d, 'MMMM')"),
        ("dayname(d)", "date_format(d, 'EEEE')"),
        ("starts_with(code, 'E11')", "startswith(code, 'E11')"),
        ("strpos(t, chr(10))", "instr(t, chr(10))"),
        ("CAST(n AS VARCHAR)", "CAST(n AS STRING)"),
        ("CAST(n AS VARCHAR(10))", "CAST(n AS VARCHAR(10))"),
        ('x AS "date"', "x AS `date`"),
        (
            "CAST(unnest(generate_series(CAST(a AS TIMESTAMP), CAST(b AS TIMESTAMP), INTERVAL 1 DAY)) AS DATE)",
            "explode(sequence(CAST(a AS DATE), CAST(b AS DATE), INTERVAL 1 DAY))",
        ),
    ],
)
def test_rewrites(duckdb: str, spark: str) -> None:
    assert to_spark_sql(f"SELECT {duckdb}") == f"SELECT {spark}"


@pytest.mark.parametrize(
    ("sql", "fragment"),
    [
        ("SELECT list_value(1)", "list_value("),
        ("SELECT x::INT", "::"),
        ("SELECT * EXCLUDE (a) FROM t", "EXCLUDE"),
        ("SELECT CAST(x AS TIMESTAMPTZ)", "TIMESTAMPTZ"),
        ("SELECT try_strptime(a || b, '%Y')", "try_strptime("),
        ("SELECT strftime(d, '%j')", "unsupported strptime/strftime format"),
        ("SELECT 'a\"b'", "double-quoted"),
    ],
)
def test_unsupported_constructs_fail_generation(sql: str, fragment: str) -> None:
    with pytest.raises(SparkDialectError, match=fragment.replace("(", r"\(")):
        to_spark_sql(sql)


def test_comments_are_not_parsed_as_sql() -> None:
    assert to_spark_sql('-- rows we exclude :: "quoted"\nSELECT 1').endswith("SELECT 1")


def test_every_packaged_medallion_query_has_a_spark_form() -> None:
    specs = SILVER_MASTER_SPECS + SILVER_SPECS + GOLD_SPECS["hc_lab"] + GOLD_SPECS["core_star"]
    for spec in specs:
        assert to_spark_sql(read_sql(spec.sql_file))


def test_git_source_format() -> None:
    text = render_notebook_content(
        [Cell("markdown", "# Title\n\ntext"), Cell("parameters", "A = 1"), Cell("code", "print(A)")]
    )
    lines = text.splitlines()
    assert lines[0] == "# Fabric notebook source"
    assert "# MARKDOWN ********************" in lines and "# # Title" in lines
    assert (
        "# PARAMETERS CELL ********************" in lines and "# CELL ********************" in lines
    )
    assert '# META   "language_group": "synapse_pyspark"' in lines
    assert text.count("# METADATA ********************") == 3  # kernel + two code cells


def test_reference_notebooks_match_the_guide_and_are_current(tmp_path: Path) -> None:
    notebooks = reference_notebooks(DATA_ROOT)
    assert [n.name for n in notebooks] == ["MCP_01_Bronze", "MCP_02_Silver", "MCP_03_Gold"]
    guide = (
        REPO_ROOT / "guides" / "hc-01-fabric-mcp-powerbi-medallion-lab" / "guide.yaml"
    ).read_text(encoding="utf-8")
    assert all(f"item_name: {n.name}" in guide for n in notebooks)
    committed = REPO_ROOT / "fabric" / "workspace"
    assert stale_or_missing(committed, notebooks) == []
    platform = json.loads(
        (committed / "MCP_01_Bronze.Notebook" / ".platform").read_text(encoding="utf-8")
    )
    assert platform["$schema"] == PLATFORM_SCHEMA
    assert platform["metadata"] == {
        "type": "Notebook",
        "displayName": "MCP_01_Bronze",
        "description": notebooks[0].description,
    }
    assert platform["config"]["logicalId"].startswith("00000000-0000-0000-0000-")
    bronze = (committed / "MCP_01_Bronze.Notebook" / "notebook-content.py").read_text(
        encoding="utf-8"
    )
    assert '"patients": 200' in bronze and 'RAW_PATH = "Files/raw"' in bronze
    assert "inferSchema" in bronze  # the documented design difference is explained

    assert len(stale_or_missing(tmp_path, notebooks)) == 6
    written = write_notebooks(tmp_path, notebooks)
    assert len(written) == 6 and stale_or_missing(tmp_path, notebooks) == []
    written[0].write_text("edited", encoding="utf-8")
    assert stale_or_missing(tmp_path, notebooks) == [written[0]]


def test_notebooks_cli(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    assert main(["notebooks", "check"]) == 0
    assert "Reference notebooks: OK" in capsys.readouterr().out
    monkeypatch.setenv("FFIA_DEFINITIONS_ROOT", str(tmp_path))
    assert main(["notebooks", "check"]) == 1
    assert "is stale" in capsys.readouterr().err
    assert main(["notebooks", "render"]) == 0
    assert main(["notebooks", "check"]) == 0
