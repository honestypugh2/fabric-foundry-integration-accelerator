"""Research registry: authoritative sources behind every architecture decision."""

from fabric_foundry_accelerator.research.sources import (
    SourceRecord,
    SourceRegistry,
    SourceStatus,
    load_registry,
    render_markdown,
)

__all__ = ["SourceRecord", "SourceRegistry", "SourceStatus", "load_registry", "render_markdown"]
