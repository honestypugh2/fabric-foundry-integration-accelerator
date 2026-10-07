# Synthetic data (no PHI, no PII)

Seeded, deterministic and obviously fictional healthcare data for analytics education. Names,
places, providers, facilities and payers are invented. IDs carry a `SYN-` prefix. The state code
is `ZZ`, and ZIP codes start with `000`. Diagnosis codes reuse the public ICD-10-CM vocabulary
as labels only. **Nothing here is clinical guidance**, and every demonstration metric is a
synthetic analytical definition.

## Layout

| Path | Committed | Contents |
|---|---|---|
| `raw/<profile>/` | ✅ | Source CSVs + `manifest.json` (rows, columns, SHA-256, injected quirks, observation cutoff) |
| `semantic/<profile>/semantic-model.yaml` | ✅ | Semantic model contract: tables, relationships, measures (local SQL and reference DAX), vocabulary |
| `expected/<profile>.json` | ✅ | Expected baseline: row counts per layer, Silver diagnostics, reconciliation totals, every measure |
| `bronze/`, `silver/`, `gold/` `<profile>/*.parquet` | ❌ (built) | Local lakehouse layers produced by `ffia data build` |
| `recovery/scenario.yaml` | ✅ | Open Mirroring recovery drill definition |
| `recovery/runs/` | ❌ (built) | Landing-zone files, snapshots and manifests from `ffia recovery run` |

## Dataset profiles

| Profile | Purpose | Sources | Gold model |
|---|---|---|---|
| `core-healthcare-v1` | Baseline accelerator dataset | 9 entities: 7 sources plus `facilities` and `payers` masters | Star schema with **physical role-playing date dimensions** (`dim_date_admission`, `dim_date_discharge`, `dim_date_claim`) |
| `hc-lab-7file-v1` | Use-Case Guide HC-01 | 7 sources whose counts match the guide baseline (200 / 1,025 / 428 / 1,025 / 4,299 / 643 / 150) | 6 `gold_` tables + 4 `dim_` tables (24 tables in total with Bronze and Silver) |

## Deliberate data-quality quirks

The Silver diagnostics must detect each of these exactly. Tests assert that the detected
counts equal the injected counts.

| Quirk | Count | Lesson |
|---|---|---|
| Conditions with blank `encounter_id` | all | A patient-level problem list; never invent encounter links |
| Notes containing a literal `\n` sequence | 56 (HC-01) | Preserve source text; `multiLine` parsing is defensive, not evidence of real newlines |
| Overlapping encounters | 3 | Identify separately from readmissions |
| Recorded LOS ≠ discharge − admission | 4 | Use the actual `discharge_date`; never approximate it |
| Blank `total_charges` | 5 | Agree blank handling (Average Charges per Encounter excludes blanks from both sides) |
| Zero `claim_amount` | 3 | Guard ratio denominators |
| Out-of-range vital values | 6 | Range checks report issues and never label a clinical condition |
| Medication end date before start date | 3 | Chronology checks |

## Commands

```bash
source .venv/bin/activate
ffia data generate --check          # committed CSVs equal the generator output (byte for byte)
ffia data build                      # Bronze -> Silver -> Gold Parquet + all checks + baseline comparison
ffia data build --verbose            # print every check
ffia data export --profile hc-lab-7file-v1 --dest ~/hc-01-lab/data/raw   # copy CSVs + SHA256SUMS
ffia recovery run                    # Open Mirroring snapshot + incremental + restore drill (SIMULATED)
```

Every result from the Local Fabric Educational Provider is labeled `LOCAL` (data reads) or
`SIMULATED` (recovery drill), with `cloud_operation_performed: false`. It is an educational
analog of Fabric, not a Fabric emulator.
