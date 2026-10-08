# Fabric Git-format item definitions

Reviewed item definitions in the Fabric Git source format, for repo-first agentic change
(Pattern 20). The scoped writer creates a notebook item **only** from a definition in this folder.

| Item | Purpose |
|---|---|
| `MCP_01_Bronze.Notebook/` | Land the seven raw CSVs as `bronze_` Delta tables, validating counts |
| `MCP_02_Silver.Notebook/` | Typed, row-preserving Silver tables and data-quality diagnostics |
| `MCP_03_Gold.Notebook/` | Gold grains, dimensions, missing-key checks and reconciliation |

Each folder has `notebook-content.py` (PySpark, `fabricGitSource` format) and `.platform` (with a
synthetic logical ID). No workspace or lakehouse ID is stored: attach the default lakehouse when
you open the notebook.

- **Generated, not hand-edited:** `ffia notebooks render` builds them from the same SQL the
  offline DuckDB build runs; `ffia notebooks check` (in validate and CI) fails when they drift.
- **Verified LOCAL** on Apache Spark 3.5.9 (Fabric Runtime 1.3's Spark line) with
  `scripts/verify_spark_notebooks.py`: all 85 checks pass against the committed baseline.
- Running them in Fabric **REQUIRES TENANT VALIDATION**.

The HC-01 guide asks learners to draft these notebooks with Copilot or Claude Code; these are the
reviewed reference versions to compare against, not a replacement for that exercise.
