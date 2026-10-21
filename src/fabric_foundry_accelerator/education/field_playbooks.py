"""Render self-contained audience playbooks from structured educational content."""

import argparse
import sys
from html import escape
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.education.interactive_architecture import render_library
from fabric_foundry_accelerator.education.playbook_bundle import render_bundle
from fabric_foundry_accelerator.education.talktrack_commands import rendered

REPOSITORY = "https://github.com/honestypugh2/fabric-foundry-integration-accelerator/blob/main/"
SLUG = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class PlaybookLink(BaseModel):
    """A repository-relative asset link."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    title: str = Field(min_length=1)
    path: str = Field(pattern=r"^[A-Za-z0-9_./-]+(?:#[a-z0-9-]+)?$")


class PlaybookCard(BaseModel):
    """One explanatory card, optionally with a command and asset links."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    title: str = Field(min_length=1)
    label: str = Field(min_length=1)
    body: str = Field(min_length=1)
    steps: tuple[str, ...] = ()
    command: str | None = None
    links: tuple[PlaybookLink, ...] = ()


class PlaybookSection(BaseModel):
    """An anchored section in a playbook."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str = Field(pattern=SLUG)
    title: str = Field(min_length=1)
    intro: str | None = None
    cards: tuple[PlaybookCard, ...] = Field(min_length=1)


class FieldPlaybook(BaseModel):
    """A standalone audience page."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    id: Literal["customer", "se-developer"]
    audience: str
    title: str
    subtitle: str
    promise: str
    sections: tuple[PlaybookSection, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_sections(self) -> Self:
        """Reject ambiguous navigation anchors."""
        if len({section.id for section in self.sections}) != len(self.sections):
            raise ValueError("Playbook section IDs must be unique")
        return self


class PlaybookRelease(BaseModel):
    """The structured field-playbook release."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    version: Literal[1]
    as_of: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    summary: str
    sources: tuple[str, ...] = Field(min_length=1)
    playbooks: tuple[FieldPlaybook, ...] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def both_audiences(self) -> Self:
        """Require exactly one page for each supported audience."""
        if {page.id for page in self.playbooks} != {"customer", "se-developer"}:
            raise ValueError("Release must include customer and se-developer playbooks")
        return self


class SourceLink(BaseModel):
    """Only the source-registry fields used by a bibliography."""

    id: str
    title: str
    url: HttpUrl


class SourceLinks(BaseModel):
    """A projection of the authoritative registry."""

    sources: tuple[SourceLink, ...]


STYLE = """
:root{color-scheme:dark;--bg:#101826;--panel:#1c293c;--text:#f2f5fb;--muted:#c4cfdf;
--accent:#a8edce;--line:#405470}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:1.5rem}
body{margin:0;background:var(--bg);color:var(--text);font:17px/1.6 system-ui,sans-serif}
a{color:var(--accent);text-underline-offset:.2em}a:hover{text-decoration-thickness:3px}
:focus-visible{outline:3px solid #ffdb83;outline-offset:5px}
.skip{position:absolute;left:1rem;top:-8rem}.skip:focus{top:1rem;background:var(--bg);z-index:3}
.wrap{max-width:1180px;margin:auto;padding:0 1.5rem}
header{padding:4rem 0 2.5rem;background:linear-gradient(135deg,#173e48,#1a274b)}
.eyebrow{letter-spacing:.13em;text-transform:uppercase;font-size:.8rem;color:var(--accent)}
h1{font-size:clamp(2.3rem,6vw,4.5rem);line-height:1.08;max-width:900px;margin:.7rem 0}
h2{font-size:1.85rem;line-height:1.25}h3{font-size:1.2rem;line-height:1.35;margin:.8rem 0}
.lead{font-size:1.3rem;max-width:850px}.muted{color:var(--muted)}
.notice{border-left:4px solid var(--accent);padding:.6rem 1rem;background:#122431}
nav{padding:1rem 0;border-bottom:1px solid var(--line)}
nav ul{display:flex;flex-wrap:wrap;gap:.7rem 1.5rem;list-style:none;padding:0;margin:0}
section{padding:2rem 0;border-bottom:1px solid var(--line)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,310px),1fr));gap:1rem}
article{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:1.5rem}
.badge{display:inline-block;font-size:.75rem;font-weight:700;letter-spacing:.06em;
background:#163c38;color:#b9f4db;border:1px solid #598778;border-radius:999px;padding:.2rem .65rem}
article p{color:var(--muted)}li+li{margin-top:.4rem}ul{padding-left:1.2rem}
pre{background:#0c1420;border:1px solid var(--line);padding:1rem;border-radius:8px;
overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;font-size:.85rem}
details{margin-top:1rem}summary{cursor:pointer;font-weight:650;color:var(--accent)}
.links{list-style:none;padding:0}.links a{display:inline-block;padding:.25rem 0}
footer{padding:2rem 0 3rem;font-size:.9rem}.sources{columns:2}
@media(max-width:650px){header{padding-top:2.5rem}.wrap{padding:0 1rem}.sources{columns:1}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{:root{color-scheme:light}body{background:white;color:black;font-size:11pt}
header{background:white}article{background:white;color:black;break-inside:avoid}
article p,.muted{color:#333}a{color:#174936}.badge{color:black;background:white}
nav,.skip{display:none}pre{background:#f4f4f4;color:black}details{display:block}}
"""


def _card(card: PlaybookCard) -> str:
    steps = (
        "<ul>" + "".join(f"<li>{escape(step)}</li>" for step in card.steps) + "</ul>"
        if card.steps
        else ""
    )
    command = (
        "<details><summary>Show command or prompt</summary>"
        f"<pre><code>{escape(card.command.rstrip())}</code></pre></details>"
        if card.command
        else ""
    )
    links = (
        '<ul class="links">'
        + "".join(
            f'<li><a href="{escape(REPOSITORY + link.path, quote=True)}">'
            f"{escape(link.title)}</a></li>"
            for link in card.links
        )
        + "</ul>"
        if card.links
        else ""
    )
    return (
        f'<article><span class="badge">{escape(card.label)}</span>'
        f"<h3>{escape(card.title)}</h3><p>{escape(card.body)}</p>{steps}{command}{links}</article>"
    )


def render_playbook(
    release: PlaybookRelease, page: FieldPlaybook, sources: dict[str, SourceLink]
) -> str:
    """Render escaped, script-free HTML with no runtime or network dependency."""
    nav = "".join(
        f'<li><a href="#{section.id}">{escape(section.title)}</a></li>' for section in page.sections
    )
    sections = "".join(
        f'<section id="{section.id}" aria-labelledby="{section.id}-title">'
        f'<h2 id="{section.id}-title">{escape(section.title)}</h2>'
        + (f'<p class="muted">{escape(section.intro)}</p>' if section.intro else "")
        + '<div class="grid">'
        + "".join(_card(card) for card in section.cards)
        + "</div></section>"
        for section in page.sections
    )
    bibliography = "".join(
        f'<li><a href="{escape(str(sources[key].url), quote=True)}">'
        f"{escape(sources[key].title)}</a> <small>({escape(key)})</small></li>"
        for key in release.sources
    )
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{escape(page.promise, quote=True)}">
<title>{escape(page.title)} | Fabric + Foundry</title><style>{STYLE}</style></head>
<body><a class="skip" href="#main">Skip to content</a>
<header><div class="wrap"><p class="eyebrow">Fabric + Foundry / Field playbook</p>
<p class="muted">{escape(page.audience)} / Snapshot {escape(release.as_of)}</p>
<h1>{escape(page.title)}</h1><p class="lead">{escape(page.subtitle)}</p>
<p>{escape(page.promise)}</p><div class="notice">{escape(release.summary)}</div></div></header>
<nav class="wrap" aria-label="Playbook sections"><ul>{nav}</ul></nav>
<main id="main" class="wrap">{sections}
<section id="sources" aria-labelledby="sources-title"><h2 id="sources-title">Sources and scope</h2>
<p class="muted">Product references are documented guidance, not evidence of this lab executing.
Follow the repository's dated verification records for actual outcomes.</p>
<ul class="sources">{bibliography}</ul></section></main>
<footer class="wrap"><p>Synthetic data only. No cloud action occurs when opening this page.
These original playbook pages have no external fonts, scripts, analytics or images.
In the offline field guide, both audience pages and full workshop handouts are embedded.
Optional repository and source references need network access and any required permissions.</p>
<p>Generated from education/field-playbooks/release.yaml. Edit the structured source,
then run make playbooks. HC-01 and MFG-01 remain featured; deferred work is not removed.</p></footer>
</body></html>
"""


def load_release(root: Path) -> tuple[PlaybookRelease, dict[str, SourceLink]]:
    """Load content and reject missing sources or unsafe/nonexistent repository links."""
    release = PlaybookRelease.model_validate(
        yaml.safe_load(
            (root / "education/field-playbooks/release.yaml").read_text(encoding="utf-8")
        )
    )
    registry = SourceLinks.model_validate(
        yaml.safe_load((root / "docs/research/sources.yaml").read_text(encoding="utf-8"))
    )
    sources = {source.id: source for source in registry.sources}
    for key in release.sources:
        if key not in sources:
            raise ValueError(f"Unknown playbook source: {key}")
    output_paths = {f"docs/field-playbooks/{page.id}.html" for page in release.playbooks}
    for page in release.playbooks:
        for section in page.sections:
            for card in section.cards:
                for link in card.links:
                    relative = link.path.split("#", 1)[0]
                    path = (root / relative).resolve()
                    if not path.is_relative_to(root.resolve()):
                        raise ValueError(f"Playbook link leaves repository: {link.path}")
                    if relative not in output_paths and not path.exists():
                        raise ValueError(f"Missing playbook link: {link.path}")
    return release, sources


def main(argv: list[str] | None = None) -> int:
    """Render or check the two playbooks; failures are explicit and nonzero."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--check", action="store_true", help="check generated files without writing"
    )
    args = parser.parse_args(argv)
    release, sources = load_release(args.root)
    handouts, errors = rendered(
        Settings(
            education_root=args.root / "education",
            demos_root=args.root / "demos",
            guides_root=args.root / "guides",
            sources_path=args.root / "docs/research/sources.yaml",
            frontend_root=args.root / "frontend",
        )
    )
    if errors:
        for error in errors:
            sys.stderr.write(f"playbooks: {error}\n")
        return 1
    documents = {
        page.id: (
            "Customer playbook" if page.id == "customer" else "SE / developer playbook",
            render_playbook(release, page, sources),
        )
        for page in release.playbooks
    }
    for key, folder, title in (
        ("fabric-engineering", "fabric-copilot-level-up", "Fabric engineering workshop"),
        ("foundry-agents", "foundry-fabric-agents-workshop", "Foundry agents workshop"),
    ):
        documents[key] = (title, handouts[args.root / "demos" / folder / "index.html"])
    documents["architecture-library"] = (
        "Architecture explorer",
        render_library(args.root, STYLE),
    )
    stale = False
    for page in release.playbooks:
        path = args.root / "docs/field-playbooks" / f"{page.id}.html"
        content = render_bundle(documents, audience=page.id)
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                sys.stderr.write(f"{path} is missing or stale; run make playbooks\n")
                stale = True
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            sys.stdout.write(f"wrote {path}\n")
    if args.check and not stale:
        sys.stdout.write("Field playbooks: OK\n")
    return int(stale)


if __name__ == "__main__":
    raise SystemExit(main())
