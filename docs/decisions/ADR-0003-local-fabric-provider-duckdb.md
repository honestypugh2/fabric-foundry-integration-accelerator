# ADR-0003: Local Fabric Educational Provider on DuckDB

- Status: Accepted
- Date: 2026-10-07

## Context

The architecture must be teachable and demonstrable with no Azure subscription, Fabric
capacity, tenant or network. Learners still need a realistic analog of a lakehouse, its medallion
layers, a semantic model and an Open Mirroring landing zone. The brief forbids presenting
simulation as a real Fabric operation.

## Options

1. DuckDB over Parquet (SQL engine, CSV parsing and Parquet I/O in one dependency)
2. pyarrow + pandas transforms
3. Local Spark (PySpark)
4. Mock-only responses with no real data processing

## Decision

- The **Local Fabric Educational Provider** uses **DuckDB 1.5.6** over Parquet.
- Medallion logic is one SQL file per output table under
  `src/fabric_foundry_accelerator/synthetic/sql/`.
- It implements the async `FabricProvider` port (read-only).
- Every result is wrapped in an `ExecutionEnvelope` labeled `LOCAL` or `SIMULATED`, with
  `cloud_operation_performed=False`, a simulation notice and the equivalent Fabric service.
- The envelope model **rejects** non-cloud labels that claim a cloud operation, and rejects
  LIVE labels that claim none.

## Rationale

- DuckDB covers CSV (with correct quote and escape handling), SQL and Parquet in one stable
  dependency. Its typing passes Pyright strict.
- A local build of both profiles takes under a second.
- SQL files are readable teaching artifacts and map closely to Spark SQL in Fabric notebooks.
- pyarrow was planned in Phase 0 but is **not needed**, because DuckDB reads and writes Parquet
  natively. It is not added (no unused dependencies).
- Local Spark needs a JVM and is heavy for offline laptops.
- Mock-only responses would teach nothing about data correctness.

## Trade-offs

- Spark SQL dialect differences must be handled when writing the Fabric notebook equivalents
  (Phase 5).
- DuckDB is not Delta Lake. Delta concepts (ACID, time travel) are taught in documentation
  rather than emulated.

## Security impact

- The provider exposes no free-form SQL, file paths or write operations.
- Table names are validated against the built catalog, and identifiers are quoted.
- Previews are capped at 100 rows.
- Measures run only by name from the committed semantic model.

## Operations impact

- `ffia data build` regenerates the local layers.
- Built Parquet is git-ignored.
- Committed raw CSVs and expected baselines make results reproducible.

## Offline impact

- The whole data path runs with sockets blocked. `tests/offline` enforces this.

## Education impact

- Learners inspect SQL per table, Silver diagnostics, Gold grain checks and baselines.
- The same baseline can later be compared with a live Fabric run, which gives evidence rather
  than appearance.

## Revisit trigger

- A need for Delta-specific behavior locally (for example time travel labs).
- DuckDB stops supporting the pinned Python version.

## Authoritative references

- `fabric-medallion`, `fabric-open-mirroring-format` and `fabric-direct-lake` in
  `docs/research/sources.yaml`.
