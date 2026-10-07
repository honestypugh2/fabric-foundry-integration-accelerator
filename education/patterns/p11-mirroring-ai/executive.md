## Why it matters

Agents and analysts want **fresh** operational data — today's claims, this hour's orders — without
building and running a custom ETL for every source. Fabric Mirroring replicates supported
databases into OneLake in near real time, and **Open Mirroring** lets any application publish
change files in a documented format. That fresh context then flows through Silver and Gold to
semantic models and agents.

The risk leaders must understand: **mirroring keeps a copy current; it is not documented as a
backup.** If a mirrored table is lost or corrupted, the service cleans up processed change files
after seven days. Without your own snapshots and retained change files, the only way back may be
a full re-seed from the source.

| Question | Answer |
|---|---|
| Is it GA? | Mirroring and Open Mirroring are **GA** as of October 2026 |
| Does it carry source security? | No — row- and object-level security must be re-applied in Fabric |
| Is it a backup? | **No.** Plan snapshots, retention and restore drills explicitly |
| Where does AI help? | Explaining drill results, spotting duplicate patterns, drafting runbooks |
| Who decides recovery is complete? | Deterministic checks: row count, keys, sequence and content hash |

**Decision for leaders:** set a recovery point objective for each mirrored table and fund the
snapshot and retention that meet it. Then rehearse it.

> In this accelerator, the landing zone, mirroring engine and restore run **SIMULATED LOCALLY**
> on synthetic claims. No Fabric mirrored database is touched.
