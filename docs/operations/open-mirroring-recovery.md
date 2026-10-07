# Open Mirroring recovery

How a mirrored table can be recovered, and when it cannot.

- Run the drill offline with `ffia recovery run`.
- The scenario is defined in `data/synthetic/recovery/scenario.yaml`.
- Every statement below is tagged with an evidence category so that simulation is never
  mistaken for documented Fabric behavior.

## The scenario

1. **Initial load.** The claims source (about 1,000 rows, standing in for a conceptual
   100-million-row fact table) lands as sequence 1 without `__rowMarker__`.
2. **Daily changes.** Ten days of incremental files with update, insert, delete and upsert
   markers.
3. **Day 5 duplicates.** A source-query defect re-sends yesterday's inserts as INSERT, which
   creates duplicate keys.
4. **Day 6 remediation.** The duplicates are removed with DELETE followed by UPSERT.
5. **Day 7 snapshot.** A weekly full Parquet snapshot is taken, with its watermark sequence
   and content hash.
6. **Day 10 failure.** The mirrored table is lost.
7. **Recovery.** Restore the day-7 snapshot and replay the retained change files after the
   watermark. Validate row count, keys, ordering and content hash.
8. **Counterfactual.** Assume the weekly snapshot never ran. With only the day-0 snapshot, the
   cleanup has already purged sequences 2–4, so the mirror cannot be brought current.

## SIMULATED LOCALLY

- Landing-zone folders and files, the mirroring engine, the snapshot and restore, retention
  purging, duplicate detection and the idempotency checks all run on local files, through
  DuckDB and Parquet.
- Results are labeled `SIMULATED` with `cloud_operation_performed: false`.

## DOCUMENTED FABRIC BEHAVIOR

Source: Microsoft Learn, *Open mirroring landing zone requirements and format*.

- Each table folder has `_metadata.json` with `keyColumns`. Without keys, updates and deletes
  are not possible, and keys cannot change after they are set.
- File names are 20 digits in continuous sequence (`00000000000000000001.parquet`).
- The initial load may omit `__rowMarker__`; the whole file is then treated as INSERT.
- `__rowMarker__` must be the **last** column. Values:
  - `0` INSERT, with **no duplicate-key check**;
  - `1` UPDATE, which inserts the row if the key is missing;
  - `2` DELETE, a no-op if the key is missing;
  - `4` UPSERT.
- Rows apply in file order.
- Processed files move to `_ProcessedFiles` or `_FilesReadyToDelete` and are removed after
  **seven days**.
- Schema changes such as dropping, renaming or retyping a column require recreating the table
  folder.
- Fabric Git integration tracks item definitions and metadata. It **never stores table data**.

## REQUIRES TENANT VALIDATION

- Whether processed files remain readable for replay, and the exact cleanup timing.
- Restore and replay throughput, and snapshot export cost, at production volume.
- Mirroring is **not documented as a backup or disaster-recovery mechanism**. Do not present it
  as one.

## ASSUMPTION

- Values are stored as text.
- The service's "last file left in place" behavior is modeled with a sequence counter.
- When duplicate keys already exist, UPDATE and UPSERT replace every matching row, and DELETE
  removes every matching row.
- Replaying processed files assumes the publisher retained its own copies.
- Scale figures are extrapolated from the local snapshot size. They are estimates, not
  measurements.

## PRODUCTION RECOMMENDATION

- **Snapshots.** Take periodic full snapshots of mirrored tables (for example weekly Parquet
  exports) with a watermark sequence and a content hash. Size matching is not a content hash.
- **Change-file retention.** Retain change files on the publisher side for longer than the
  snapshot interval plus a safety margin. The 7-day service cleanup alone cannot cover a gap
  longer than seven days.
- **Replay discipline.** Replay each sequence exactly once after the watermark. INSERT-marker
  files are not idempotent. Prefer UPSERT (`4`) markers for keyed tables.
- **Duplicates.** Treat them as a source-query or data-quality issue unless evidence shows
  otherwise. Fix the publisher, then remediate with DELETE followed by UPSERT.
- **Restore checks.** After any restore, validate row counts, key uniqueness, sequence
  contiguity and the content hash before declaring recovery complete.

## PREVIEW LIMITATION

- None in this drill. Open Mirroring is GA.
