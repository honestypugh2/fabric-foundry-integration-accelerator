# ADR-0004: Synthetic dataset profiles, committed raw data and expected baselines

- Status: Accepted
- Date: 2026-10-07

## Context

The baseline accelerator needs a richer healthcare model (facility and payer masters, star
schema, physical role-playing dates). Use-Case Guide HC-01 needs seven sources whose row counts
and quirks match its documented baseline. More guides will follow. The core code must not fork
per guide or customer, and live Fabric runs need something concrete to be compared against.

## Options

1. One dataset for everything
2. One generator with **profiles** (sizes, quirks, masters, Gold model) selected by
   configuration
3. Copy each guide's public sample data into the repository

## Decision

- Use **dataset profiles**:
  - `core-healthcare-v1` is the baseline.
  - `hc-lab-7file-v1` is Guide HC-01.
- One seeded generator produces both. Silver SQL is shared, and each profile has its own Gold
  model.
- Commit, for each profile:
  - raw CSVs plus a manifest;
  - the semantic model contract;
  - an **expected baseline** (row counts, diagnostics, reconciliation, every measure).
- Build Bronze, Silver and Gold on demand. They are git-ignored.

## Rationale

- Profiles are additive: guides add a profile and a Gold model without touching the baseline.
- Committed raw data makes the offline demo work immediately after setup, and is reviewable.
- `ffia data generate --check` proves the committed data is byte-identical to the generator.
- Public guide sample data may carry no licence and could carry identifying context. Our
  generator reproduces only the documented shape and quirks.

## Trade-offs

- About 2.6 MB of CSV is committed.
- Changing the generator requires regenerating the data and baselines in the same change.

## Security impact

- The data is obviously fictional: `SYN-` IDs, the `ZZ` state code, `000` ZIP codes and
  invented names.
- `ffia privacy scan` covers the committed data.
- `dim_patient` deliberately excludes names and dates of birth.

## Operations impact

- `make data` builds and validates.
- CI verifies that the committed data still matches the generator.

## Offline impact

- No downloads are needed. Everything ships in the repository.

## Education impact

- Deliberate quirks make every Silver check meaningful.
- The baselines turn "it ran" into "it produced the right numbers".

## Revisit trigger

- A guide needs a substantially different domain model (add a profile).
- Dataset size approaches the leak scanner's 2 MB per-file limit.

## Authoritative references

- `fabric-medallion` and `fabric-direct-lake` in `docs/research/sources.yaml`.
- Phase 0 Addendum B (Use-Case Guides framework).
