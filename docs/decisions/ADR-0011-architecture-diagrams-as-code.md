# ADR-0011: Architecture diagrams as code (draw.io, Azure Architecture Center style)

- Status: Accepted
- Date: 2026-10-07

## Context

The accelerator needs detailed, dynamic architecture diagrams. They must:

- support the web app, the repository documentation and live presentations;
- match the conventions of the Azure Architecture Center and Azure GitHub reference
  implementations: official Azure icons, draw.io sources, numbered workflows, and Well-Architected
  considerations;
- never overstate what exists.

Hand-drawn diagrams drift from the code and from each other.

## Options

1. Hand-maintained draw.io files plus screenshots.
2. Mermaid only.
3. Views as validated YAML, with one shared layout engine rendering:
   - interactive SVG in the app;
   - draw.io files;
   - Mermaid and Markdown blocks in the docs.

## Decision

Option 3.

- **Views.** `education/architecture/views/*.yaml` define the diagrams: reference, production,
  system, mcp-topology, agentic-de, hc-01 and live-vs-offline. Each view has:
  - nodes on a grid, edges, zones and cross-cutting bands;
  - build-up steps and request traces;
  - Microsoft references (`aligned_to`) and pattern links.
- **Honest nodes.** Every node states whether it is implemented in this repository, planned (with
  its phase), Microsoft-documented, preview, requires tenant validation, or optional. Nodes can
  link to the component catalog for Executive–L400 descriptions, and can bind to a runtime
  capability.
- **Shared layout.** `education/layout.py` computes a deterministic layout:
  - cards on a grid;
  - orthogonal edges routed through per-owner lanes in the gutters between columns, and through
    row gaps when a straight run would cross a card;
  - a test asserts that no edge crosses another card.
- **draw.io files.** `education/drawio.py` writes multi-page `.drawio` files: the full
  architecture, then one page per build step. They use draw.io's built-in official Azure icons
  (`img/lib/azure2`), referenced by path and never copied into the repository. Fabric, GitHub
  and Claude have no draw.io icon, so they are drawn as styled cards. The first trace is numbered
  on the diagram, as in the Architecture Center.
- **Docs and drift.** `ffia diagrams render` writes `docs/architecture/diagrams/*.drawio` and the
  generated block of each architecture doc: draw.io link, Mermaid, numbered workflow, components
  table and *Aligned to*. `ffia diagrams check` fails when anything is stale, and `make validate`
  runs it.
- **App.** The web app (`/architecture/:view`) renders the same layout as accessible SVG:
  - build-up steps, request traces and a presenter cue;
  - an inspector that follows the learning level;
  - a text alternative and a draw.io download.
- **Live state.** A runtime overlay from `GET /api/v1/education/views/{id}/runtime` colors nodes
  from the control plane's actual state. Later-phase services show as NOT CONFIGURED; nothing is
  inferred in the browser.

## Rationale

- **One source:** the app, the draw.io files and the docs cannot disagree.
- **Familiar conventions:** the Azure Architecture Center layout (icons, numbered workflow,
  pillar considerations) is recognizable to architects.
- **Verified alignment:** each view cites the Microsoft guidance it follows, checked on
  2026-10-07. No single first-party Fabric + Foundry reference architecture exists, and the docs
  say so.

## Trade-offs

- **Layout is grid-based.** Very dense diagrams need layout changes in YAML rather than free
  drawing. Hand-edited draw.io changes are overwritten by `ffia diagrams render`.
- **No icons in the app.** The app draws icon-free cards, because shipping icon files to the
  browser would mean redistributing them; the draw.io files carry the icons.

## Security impact

- Diagrams contain no tenant, workspace or customer identifiers, and they go through the privacy
  scan.
- The runtime overlay exposes only statuses that `/runtime/status` already shows.

## Operations impact

- Change a view, then run `make diagrams`. `make validate` fails on stale artifacts.

## Offline impact

- Everything renders offline. Only opening the draw.io files with Azure icons needs draw.io.

## Education impact

- Presenters build diagrams layer by layer and trace requests; each guide step highlights its
  part of the guide diagram.

## Revisit trigger

- Microsoft publishes a first-party Fabric + Foundry reference architecture.
- draw.io adds official Microsoft Fabric icons.

## Authoritative references

- `baseline-foundry-chat`, `basic-foundry-chat`, `caf-agent-data-architecture`, `fabric-medallion`,
  `fabric-deployment-patterns`, `fabric-waf`, `apim-mcp` and `foundry-mcp-governance` in
  `docs/research/sources.yaml`.
- [reference-architecture.md](../architecture/reference-architecture.md)
