"""Run the committed Fabric reference notebooks on a local Apache Spark 3.5 session.

This is a development-time check, not part of the offline demo or CI. It needs PySpark 3.5 and a
Java 17 runtime, which are not project dependencies (Fabric Runtime 1.3 runs Spark 3.5). It
executes the code cells of each committed ``notebook-content.py`` exactly as written. It overrides
only two parameters:

- ``RAW_PATH`` points at the local synthetic CSVs;
- ``TABLE_FORMAT`` is ``parquet``, because Delta Lake is not installed locally.

Every validation in the notebooks must pass. The result is LOCAL evidence that the SQL and code run
on Spark 3.5. It is not evidence that anything ran in Fabric.

Usage:
    JAVA_HOME=<jdk17> <python-with-pyspark-3.5> scripts/verify_spark_notebooks.py
"""

import re
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ("MCP_01_Bronze", "MCP_02_Silver", "MCP_03_Gold")
RAW = ROOT / "data" / "synthetic" / "raw" / "hc-lab-7file-v1"
MARKER = re.compile(r"^# (MARKDOWN|PARAMETERS CELL|CELL|METADATA) \*+$")


def code_cells(path: Path) -> list[tuple[str, str]]:
    """Return (kind, source) for every code and parameters cell."""
    cells: list[tuple[str, str]] = []
    kind: str | None = None
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        found = MARKER.match(line)
        if found:
            if kind in ("CELL", "PARAMETERS CELL"):
                cells.append((kind, "\n".join(lines)))
            kind, lines = found[1], []
            continue
        lines.append(line)
    return cells


def main() -> int:
    """Run Bronze, Silver and Gold in one Spark session; return a process exit code."""
    from pyspark.sql import SparkSession  # noqa: PLC0415 - optional runtime

    warehouse = tempfile.mkdtemp(prefix="ffia-spark-")
    spark = (
        SparkSession.builder.master("local[4]")
        .appName("ffia-notebook-verify")
        .config("spark.sql.warehouse.dir", warehouse)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    print(f"Apache Spark {spark.version} (local). Warehouse: {warehouse}")
    failures = 0
    for name in NOTEBOOKS:
        path = ROOT / "fabric" / "workspace" / f"{name}.Notebook" / "notebook-content.py"
        print(f"\n=== {name} ({path.relative_to(ROOT)})")
        namespace: dict[str, object] = {"spark": spark}
        started = time.monotonic()
        try:
            for kind, source in code_cells(path):
                exec(compile(source, f"{name}:{kind}", "exec"), namespace)  # noqa: S102 - committed, reviewed notebook code
                if kind == "PARAMETERS CELL":
                    namespace["RAW_PATH"] = RAW.as_uri()
                    namespace["TABLE_FORMAT"] = "parquet"
        except Exception as error:  # noqa: BLE001 - report and continue to the summary
            failures += 1
            print(f"FAILED: {type(error).__name__}: {str(error)[:2000]}")
        print(f"--- {name}: {time.monotonic() - started:.1f}s")
    spark.stop()
    print("\nRESULT:", "PASSED" if failures == 0 else f"{failures} notebook(s) FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
