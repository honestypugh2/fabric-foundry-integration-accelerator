# Guide HC-01: Fabric MCP + Power BI medallion lab (healthcare, synthetic)

VS Code + GitHub Copilot agent mode with the local Fabric MCP server, remote Fabric Spark notebooks (Bronze, Silver, Gold), a Direct Lake semantic model edited through Power BI Modeling MCP and authoring skills, DAX reconciliation, and a two-page report. Every step has a Claude Code path and an offline equivalent. Synthetic data only; no clinical rules.

Populated in: Phase 2-7.

## Available now (Phase 2)

| Asset | Where | Notes |
|---|---|---|
| Source data | Dataset profile `hc-lab-7file-v1` | Same counts and quirks as the guide baseline: 200 / 1,025 / 428 / 1,025 / 4,299 / 643 / 150 |
| Expected baseline | `data/synthetic/expected/hc-lab-7file-v1.json` | Row counts for all 24 tables, Silver diagnostics, reconciliation totals and every measure |
| Semantic model contract | `data/synthetic/semantic/hc-lab-7file-v1/semantic-model.yaml` | 7 tables, star relationships, measure contracts with reference DAX; Bed Occupancy excluded |
| Local reference build | `ffia data build --profile hc-lab-7file-v1` | Offline Bronze/Silver/Gold to compare against the live Fabric run |

Copy the data into a separate lab project folder, as the guide recommends:

```bash
ffia data export --profile hc-lab-7file-v1 --dest ~/hc-01-lab/data/raw
cd ~/hc-01-lab/data/raw && sha256sum -c SHA256SUMS
```
