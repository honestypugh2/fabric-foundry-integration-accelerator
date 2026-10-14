"""Offline checks for standalone customer and developer playbooks."""

from html.parser import HTMLParser
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from fabric_foundry_accelerator.education import field_playbooks as playbooks

ROOT = Path(__file__).resolve().parents[2]


class PageInspection(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.anchors: list[str] = []
        self.remote_resources: list[str] = []
        self.scripts = 0
        self.headings = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        identifier = attributes.get("id")
        href = attributes.get("href")
        if identifier is not None:
            self.ids.append(identifier)
        if tag == "a" and href is not None and href.startswith("#"):
            self.anchors.append(href[1:])
        if tag in {"script", "img", "iframe", "link"}:
            self.remote_resources.append(tag)
        if tag == "script":
            self.scripts += 1
        if tag == "h1":
            self.headings += 1


def test_current_release_has_both_audiences_and_honest_boundaries() -> None:
    release, sources = playbooks.load_release(ROOT)
    assert {page.id for page in release.playbooks} == {"customer", "se-developer"}
    for page in release.playbooks:
        html = playbooks.render_playbook(release, page, sources)
        assert "HC-01" in html and "MFG-01" in html and "DQ-01" in html
        assert "Claude" in html and "DOCUMENTED ONLY" in html
        assert "deferred" in html
        assert "tool-reported" in html or "tool reported" in html
        assert "No cloud action occurs" in html
        assert all(key in html for key in release.sources)
        inspection = PageInspection()
        inspection.feed(html)
        assert inspection.headings == 1
        assert not inspection.scripts
        assert not inspection.remote_resources
        assert len(inspection.ids) == len(set(inspection.ids))
        assert set(inspection.anchors) <= set(inspection.ids)
        assert "prefers-reduced-motion" in html and ":focus-visible" in html


def test_rendering_escapes_content_and_commands() -> None:
    release, sources = playbooks.load_release(ROOT)
    card = playbooks.PlaybookCard(
        title="<script>sample</script>",
        label='quoted "label"',
        body="A & B < C",
        command="echo '<example>'",
        steps=("<b>not markup</b>",),
        links=(playbooks.PlaybookLink(title="<link>", path="README.md"),),
    )
    section = playbooks.PlaybookSection(id="example", title="A < B", cards=(card,))
    page = release.playbooks[0].model_copy(
        update={"sections": (section,), "promise": '"quoted" <description>'}
    )
    html = playbooks.render_playbook(release, page, sources)
    assert "<script>" not in html
    assert "&lt;script&gt;sample&lt;/script&gt;" in html
    assert "A &amp; B &lt; C" in html
    assert "&lt;b&gt;not markup&lt;/b&gt;" in html
    assert "&lt;example&gt;" in html
    assert "&quot;quoted&quot; &lt;description&gt;" in html


def test_duplicate_sections_and_audiences_are_rejected() -> None:
    release, _ = playbooks.load_release(ROOT)
    page = release.playbooks[0]
    data = page.model_dump()
    data["sections"] = [page.sections[0].model_dump()] * 2
    with pytest.raises(ValidationError, match="section IDs must be unique"):
        playbooks.FieldPlaybook.model_validate(data)
    data = release.model_dump()
    data["playbooks"] = [page.model_dump()] * 2
    with pytest.raises(ValidationError, match="customer and se-developer"):
        playbooks.PlaybookRelease.model_validate(data)


@pytest.mark.parametrize("path", ["javascript:example", "https://example.invalid", 'README.md"'])
def test_non_repository_link_shapes_are_rejected(path: str) -> None:
    with pytest.raises(ValidationError):
        playbooks.PlaybookLink(title="Unsafe link", path=path)


def scratch_content(tmp_path: Path, release: playbooks.PlaybookRelease) -> None:
    content = tmp_path / "education/field-playbooks"
    registry = tmp_path / "docs/research"
    content.mkdir(parents=True)
    registry.mkdir(parents=True)
    (content / "release.yaml").write_text(yaml.safe_dump(release.model_dump(mode="json")))
    (registry / "sources.yaml").write_text(
        (ROOT / "docs/research/sources.yaml").read_text(encoding="utf-8")
    )


def test_unknown_source_is_explicitly_rejected(tmp_path: Path) -> None:
    release, _ = playbooks.load_release(ROOT)
    scratch_content(tmp_path, release.model_copy(update={"sources": ("missing-source",)}))
    with pytest.raises(ValueError, match="Unknown playbook source"):
        playbooks.load_release(tmp_path)


@pytest.mark.parametrize(
    ("path", "error"),
    [("../outside.md", "leaves repository"), ("missing.md", "Missing playbook link")],
)
def test_missing_and_out_of_repository_links_fail(tmp_path: Path, path: str, error: str) -> None:
    release, _ = playbooks.load_release(ROOT)
    card = playbooks.PlaybookCard(
        title="Example",
        label="LOCAL",
        body="Example",
        links=(playbooks.PlaybookLink(title="Example", path=path),),
    )
    section = playbooks.PlaybookSection(id="example", title="Example", cards=(card,))
    pages = tuple(page.model_copy(update={"sections": (section,)}) for page in release.playbooks)
    scratch_content(tmp_path, release.model_copy(update={"playbooks": pages}))
    with pytest.raises(ValueError, match=error):
        playbooks.load_release(tmp_path)


def test_render_check_detects_missing_and_stale_pages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    release, sources = playbooks.load_release(ROOT)

    def load_content(
        _root: Path,
    ) -> tuple[playbooks.PlaybookRelease, dict[str, playbooks.SourceLink]]:
        return release, sources

    monkeypatch.setattr(playbooks, "load_release", load_content)
    args = ["--root", str(tmp_path)]
    assert playbooks.main([*args, "--check"]) == 1
    assert "missing or stale" in capsys.readouterr().err
    assert playbooks.main(args) == 0
    assert playbooks.main([*args, "--check"]) == 0
    page = tmp_path / "docs/field-playbooks/customer.html"
    page.write_text("stale")
    assert playbooks.main([*args, "--check"]) == 1
    assert page.read_text() == "stale"


def test_committed_html_matches_structured_source() -> None:
    assert playbooks.main(["--root", str(ROOT), "--check"]) == 0
