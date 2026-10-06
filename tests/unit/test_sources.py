from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from fabric_foundry_accelerator.research.sources import (
    DEFAULT_REGISTRY_PATH,
    DEFAULT_RENDERED_PATH,
    SourceRecord,
    SourceRegistry,
    SourceStatus,
    load_registry,
    render_markdown,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _record(**overrides: object) -> SourceRecord:
    base: dict[str, object] = {
        "id": "example-source",
        "title": "Example source",
        "url": "https://learn.microsoft.com/example",
        "publisher": "Microsoft",
        "retrieved_date": date(2026, 10, 5),
        "technology": "Fabric",
        "associated_patterns": ["P01"],
        "status": SourceStatus.GA,
        "key_architecture_statement": "Statement | with pipe",
        "implementation_relevance": "Relevance",
        "security_implications": "Security",
        "limitations": "Limits",
        "fallback": "Fallback",
    }
    base.update(overrides)
    return SourceRecord.model_validate(base)


def test_repository_registry_is_valid_and_rendered_file_is_current() -> None:
    registry = load_registry(REPO_ROOT / DEFAULT_REGISTRY_PATH)
    assert len(registry.sources) >= 20
    rendered = (REPO_ROOT / DEFAULT_RENDERED_PATH).read_text(encoding="utf-8")
    assert rendered == render_markdown(registry)


def test_http_urls_are_rejected() -> None:
    with pytest.raises(ValidationError, match="https"):
        _record(url="http://example.com/insecure")


def test_duplicate_ids_are_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate source id"):
        SourceRegistry(version=1, sources=[_record(), _record()])


def test_render_escapes_pipes_and_marks_missing_values() -> None:
    markdown = render_markdown(SourceRegistry(version=1, sources=[_record()]))
    assert "Statement \\| with pipe" in markdown
    assert "| Last updated | — |" in markdown
    assert "| Associated patterns | P01 |" in markdown
    assert '<a id="example-source"></a>' in markdown
