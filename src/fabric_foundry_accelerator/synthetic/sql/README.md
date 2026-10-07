# Medallion SQL (local DuckDB engine)

One file per output table. Each file contains a single `SELECT` (or `WITH … SELECT`) that the
builder wraps in `CREATE TABLE <name> AS …`. Tables whose name starts with `_` are staging tables
and are not written to Parquet.

- `silver/`: typed, conformed Silver tables shared by every profile.
- `gold_shared/`: Gold logic reused across profiles (date spine, population health, encounter
  summary, readmissions).
- `gold_hc_lab/`: Gold outputs for Use-Case Guide HC-01 (six `gold_` tables and four `dim_`
  tables).
- `gold_core_star/`: the baseline star schema with physical role-playing date dimensions.

The Fabric notebook equivalents (PySpark / Spark SQL) are part of the live path. Every metric here
is a **synthetic analytical demonstration**, not a clinical definition.
