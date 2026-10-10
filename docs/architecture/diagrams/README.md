# Architecture PNGs and editable draw.io sources

**LOCAL asset generation.** These PNGs were exported directly from the generated `.drawio`
files with draw.io Desktop 32.4.1. They are not rasterized app SVGs or cloud execution evidence.
The renderer was obtained from the official draw.io Desktop release and its package checksum
was verified against the release's SHA-256 manifest. It is not a runtime dependency.

| View | PNG for docs and presentations | Editable source |
|---|---|---|
| Repository runtime | [system.png](system.png) | [system.drawio](system.drawio) |
| Fabric + Foundry reference | [reference.png](reference.png) | [reference.drawio](reference.drawio) |
| Production recommendation, not deployed | [production.png](production.png) | [production.drawio](production.drawio) |
| MCP topology | [mcp-topology.png](mcp-topology.png) | [mcp-topology.drawio](mcp-topology.drawio) |
| Copilot maturity ladder | [agentic-de.png](agentic-de.png) | [agentic-de.drawio](agentic-de.drawio) |
| Fabric engineering use case | [hc-01.png](hc-01.png) | [hc-01.drawio](hc-01.drawio) |
| Foundry sales-insights use case | [mfg-01.png](mfg-01.png) | [mfg-01.drawio](mfg-01.drawio) |
| Live-first and offline routing | [live-vs-offline.png](live-vs-offline.png) | [live-vs-offline.drawio](live-vs-offline.drawio) |
| Focused foundations | [theory-to-tools.png](theory-to-tools.png) | [theory-to-tools.drawio](theory-to-tools.drawio) |
| Separate integration paths | [integration-paths.png](integration-paths.png) | [integration-paths.drawio](integration-paths.drawio) |

## Regenerate after an architecture change

Edit the corresponding [structured view](../../../education/architecture/views/), then run
`ffia diagrams render`. Do not edit generated draw.io files or generated Markdown blocks by
hand. PNG embeds sit outside the generated blocks so rendering preserves them.

With the verified Desktop executable available as `drawio`, run from the repository root:

```bash
for view in system reference production mcp-topology agentic-de hc-01 mfg-01 live-vs-offline theory-to-tools integration-paths; do
  drawio --disable-gpu --export --format png --page-index 1 \
    --scale 1.5 --border 24 --embed-diagram --theme light --disable-update \
    --output "docs/architecture/diagrams/$view.png" \
    "docs/architecture/diagrams/$view.drawio" || exit 1
done
ffia diagrams check
```

For headless Linux, prefix the `drawio` invocation with `xvfb-run -a` when no display is
available. Software rendering avoids the GPU-process failure encountered during export.
In Desktop 32.4.1, `--page-index 1` selects the full architecture page. Each PNG embeds that
editable page, not the entire multi-page file. Open the `.drawio` source for the subsequent
pages containing the progressive teaching steps.

Open the resulting PNGs to check readability, connector labels and cropping before using them.
The diagram check validates generated sources and Markdown, not PNG freshness or visual quality.
Re-export after every source change. For a short workshop explanation, use the progressive
pages or a focused diagram rather than shrinking a dense full architecture onto one slide.

## Evidence and privacy

Static diagram states describe implementation, documented behavior, planned work and preview
features. They are not a current health probe or proof of a tool call. Use the application
runtime overlay and [phase-verification evidence](../../operations/phase-verification.md) for
that distinction. Keep real tenant and resource identifiers out of diagram sources, embedded
metadata and screenshots.
