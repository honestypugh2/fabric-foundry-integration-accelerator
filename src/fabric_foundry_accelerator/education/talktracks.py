"""Talk tracks as validated data, rendered to self-contained HTML handouts.

A talk track (``demos/<id>/talk-track.yaml``) is a presenter's script for a demo or workshop. It
lists the entry points (portal, web app, VS Code, terminal), prerequisites, timing, reference
architectures, patterns, and timed parts made of steps. Each step has where to go, what to say,
what to show, a checkpoint, an honest result label and a fallback. It also carries anticipated
questions with labeled answers.

``render_html`` writes one file with no scripts and no external assets. Architecture diagrams are
embedded as SVG generated from the same view YAML as the app and the draw.io files, so the handout
cannot drift from the architecture.
"""

import html
import re
from importlib.resources import files
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from fabric_foundry_accelerator.education.diagrams import DiagramView
from fabric_foundry_accelerator.education.svg import render_svg, workflow
from fabric_foundry_accelerator.patterns.catalog import ArchitecturePattern

ResultLabel = Literal[
    "LIVE",
    "LOCAL",
    "SIMULATED",
    "PREVIEW",
    "DOCUMENTED",
    "REQUIRES TENANT VALIDATION",
    "DISCUSSION",
]
LABEL_MEANING: dict[str, str] = {
    "LIVE": "A real call to the demo tenant, observed on screen.",
    "LOCAL": "Ran on the presenter's laptop over synthetic data; no cloud call.",
    "SIMULATED": "A local simulation of a cloud operation; nothing changed in a tenant.",
    "PREVIEW": "Depends on a preview feature or API; behavior can change.",
    "DOCUMENTED": "Microsoft or GitHub documentation, cited; not run in this demo.",
    "REQUIRES TENANT VALIDATION": "Built and tested offline; not yet observed in a tenant.",
    "DISCUSSION": "Conversation with the customer; no system involved.",
}
_SLUG = r"^[a-z0-9]+(-[a-z0-9]+)*$"
TALK_TRACK_FILE = "talk-track.yaml"
HTML_FILE = "index.html"


class EntryPoint(BaseModel):
    """Where the presenter works: a portal, the web app, VS Code or a terminal."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    name: str
    where: str
    purpose: str


class Prerequisite(BaseModel):
    """A group of things to prepare before the session."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str
    items: tuple[str, ...] = Field(min_length=1)


class ArchitectureRef(BaseModel):
    """An architecture view to embed, with the presenter's caption."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    view: str
    caption: str


class Step(BaseModel):
    """One presenter step."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str
    entry: str
    path: str
    label: ResultLabel
    say: tuple[str, ...] = Field(min_length=1)
    show: tuple[str, ...] = ()
    check: str | None = None
    code: str | None = None
    fallback: str | None = None


class Part(BaseModel):
    """A timed segment of the session."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    title: str
    minutes: int = Field(ge=1, le=60)
    goal: str
    steps: tuple[Step, ...] = Field(min_length=1)


class Answer(BaseModel):
    """An anticipated question with a labeled answer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    q: str
    a: str
    label: ResultLabel
    sources: tuple[str, ...] = ()
    featured: bool = False


class OptionRow(BaseModel):
    """A decision, its options and the recommendation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    decision: str
    options: str
    recommendation: str


class MappingRow(BaseModel):
    """Where each need lives in the accelerator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    need: str
    asset: str


class TalkTrack(BaseModel):
    """``demos/<id>/talk-track.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    title: str
    subtitle: str
    eyebrow: str
    guide: str | None = None
    audience: str
    duration_minutes: int = Field(ge=10, le=240)
    summary: str
    objectives: tuple[str, ...] = Field(min_length=1)
    entry_points: tuple[EntryPoint, ...] = Field(min_length=1)
    prerequisites: tuple[Prerequisite, ...] = ()
    architecture: tuple[ArchitectureRef, ...] = ()
    patterns: tuple[str, ...] = ()
    parts: tuple[Part, ...] = Field(min_length=1)
    qa: tuple[Answer, ...] = ()
    options: tuple[OptionRow, ...] = ()
    reset: tuple[str, ...] = ()
    mapping: tuple[MappingRow, ...] = ()

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        errors: list[str] = []
        total = sum(p.minutes for p in self.parts)
        if total != self.duration_minutes:
            errors.append(f"parts add up to {total} minutes, not {self.duration_minutes}")
        entries = {e.id for e in self.entry_points}
        for part in self.parts:
            for step in part.steps:
                if step.entry not in entries:
                    errors.append(
                        f"{part.id}: step {step.title!r} uses unknown entry {step.entry!r}"
                    )
        if len({p.id for p in self.parts}) != len(self.parts):
            errors.append("duplicate part ids")
        if errors:
            raise ValueError(f"talk track {self.id}: " + "; ".join(errors))
        return self


def load_talk_track(path: Path) -> TalkTrack:
    """Load one talk track."""
    return TalkTrack.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_talk_tracks(demos_root: Path) -> dict[str, TalkTrack]:
    """Load every ``demos/<id>/talk-track.yaml``; the folder name must equal the id."""
    tracks: dict[str, TalkTrack] = {}
    for path in sorted(demos_root.glob(f"*/{TALK_TRACK_FILE}")):
        track = load_talk_track(path)
        if track.id != path.parent.name:
            raise ValueError(f"talk track {track.id!r} must live in demos/{track.id}/")
        tracks[track.id] = track
    return tracks


def reference_errors(
    track: TalkTrack,
    *,
    views: dict[str, DiagramView],
    patterns: dict[str, ArchitecturePattern],
    source_ids: frozenset[str],
    guide_ids: frozenset[str],
) -> list[str]:
    """Cross-file references: views, patterns, sources and the guide must exist."""
    errors = [f"unknown view {a.view!r}" for a in track.architecture if a.view not in views]
    errors += [f"unknown pattern {p!r}" for p in track.patterns if p not in patterns]
    errors += [
        f"unknown source {s!r} in answer {qa.q[:40]!r}"
        for qa in track.qa
        for s in qa.sources
        if s not in source_ids
    ]
    if track.guide is not None and track.guide not in guide_ids:
        errors.append(f"unknown guide {track.guide!r}")
    return [f"{track.id}: {e}" for e in errors]


# --------------------------------------------------------------------------- rendering
_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def _inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = _CODE.sub(lambda m: f"<code>{m[1]}</code>", out)
    return _BOLD.sub(lambda m: f"<strong>{m[1]}</strong>", out)


def _blocks(text: str) -> str:
    """Paragraphs separated by blank lines; ``- `` lines become a list; ``1. `` an ordered list."""
    chunks: list[str] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if all(line.lstrip().startswith("- ") for line in lines):
            items = "".join(f"<li>{_inline(line.lstrip()[2:])}</li>" for line in lines)
            chunks.append(f"<ul>{items}</ul>")
        elif all(re.match(r"^\s*\d+\. ", line) for line in lines):
            items = "".join(
                f"<li>{_inline(re.sub(r'^\s*\d+\. ', '', line))}</li>" for line in lines
            )
            chunks.append(f"<ol>{items}</ol>")
        else:
            chunks.append(f"<p>{_inline(' '.join(line.strip() for line in lines))}</p>")
    return "".join(chunks)


def _chip(label: str) -> str:
    css = label.lower().replace(" ", "-")
    return f'<span class="chip chip--{css}">{html.escape(label)}</span>'


def _css() -> str:
    return (
        files("fabric_foundry_accelerator.education")
        .joinpath("talktrack.css")
        .read_text(encoding="utf-8")
    )


def _section_link(anchor: str, text: str) -> str:
    return f'<a href="#{anchor}">{html.escape(text)}</a>'


def _nav(track: TalkTrack) -> str:
    links = [
        _section_link("overview", "Overview"),
        _section_link("entry-points", "Entry points"),
        _section_link("prep", "Prep"),
        _section_link("timing", "Timing"),
    ]
    if track.architecture:
        links.append(_section_link("architecture", "Architecture"))
    if track.patterns:
        links.append(_section_link("patterns", "Patterns"))
    links += [_section_link(p.id, p.title.split(":")[0]) for p in track.parts]
    if track.qa:
        links.append(_section_link("qa", "Q&A"))
    if track.options:
        links.append(_section_link("options", "Options"))
    links.append(_section_link("reset", "Reset"))
    return f'<header class="topbar"><nav aria-label="Sections">{"".join(links)}</nav></header>'


def _hero(track: TalkTrack) -> list[str]:
    out = [
        '<section class="hero">',
        f'<div class="eyebrow">{html.escape(track.eyebrow)}</div>',
        f"<h1>{html.escape(track.title)}</h1>",
        f'<p class="lead">{_inline(track.subtitle)}</p>',
        '<div class="meta">',
        f"<span>{track.duration_minutes} minutes</span>",
        f"<span>{html.escape(track.audience)}</span>",
    ]
    if track.guide:
        out.append(f"<span>Guide <code>{html.escape(track.guide)}</code></span>")
    out.append("<span>Synthetic data only</span></div></section>")
    return out


def _overview(track: TalkTrack) -> list[str]:
    out = ['<h2 id="overview">Overview</h2>', _blocks(track.summary)]
    out.append("<h3>By the end, the audience can</h3><ul>")
    out += [f"<li>{_inline(o)}</li>" for o in track.objectives]
    out.append('</ul><h3>Result labels (say them out loud)</h3><table class="legend"><tbody>')
    used = {s.label for p in track.parts for s in p.steps} | {qa.label for qa in track.qa}
    out += [
        f"<tr><td>{_chip(label)}</td><td>{html.escape(meaning)}</td></tr>"
        for label, meaning in LABEL_MEANING.items()
        if label in used
    ]
    out.append("</tbody></table>")
    out.append('<h2 id="entry-points">Entry points</h2><div class="grid">')
    out += [
        f'<div class="card entry"><h3>{html.escape(e.name)}</h3>'
        f'<p class="where">{html.escape(e.where)}</p><p>{_inline(e.purpose)}</p></div>'
        for e in track.entry_points
    ]
    out.append('</div><h2 id="prep">Prerequisites and preparation</h2>')
    for group in track.prerequisites:
        out.append(f"<h3>{html.escape(group.title)}</h3><ul>")
        out += [f"<li>{_inline(item)}</li>" for item in group.items]
        out.append("</ul>")
    return out


def _timing(track: TalkTrack) -> list[str]:
    entries = {e.id: e.name for e in track.entry_points}
    out = [
        '<h2 id="timing">Timing</h2><table><thead><tr><th>Segment</th><th>Minutes</th>'
        '<th>Entry points</th><th style="width:30%"></th></tr></thead><tbody>'
    ]
    for part in track.parts:
        names = ", ".join(sorted({entries[s.entry] for s in part.steps}))
        pct = 100 * part.minutes / track.duration_minutes
        out.append(
            f'<tr><td><a href="#{part.id}">{html.escape(part.title)}</a></td><td>{part.minutes}</td>'
            f'<td>{html.escape(names)}</td><td><div class="bar" style="width:{pct:.1f}%"></div></td></tr>'
        )
    out.append(f"<tr><th>Total</th><th>{track.duration_minutes}</th><th></th><th></th></tr>")
    out.append("</tbody></table>")
    return out


def _architecture(track: TalkTrack, views: dict[str, DiagramView]) -> list[str]:
    if not track.architecture:
        return []
    out = ['<h2 id="architecture">Reference architectures</h2>']
    for ref in track.architecture:
        view = views[ref.view]
        svg = render_svg(view, title_id=f"svg-{track.id}-{view.id}")
        out.append(
            f'<figure><div class="arch-wrap">{svg}</div><figcaption><strong>'
            f"{html.escape(view.title)}.</strong> {_inline(ref.caption)}</figcaption>"
        )
        steps = workflow(view)
        if steps:
            out.append("<h3>Workflow</h3><ol>")
            out += [f"<li>{_inline(s)}</li>" for s in steps]
            out.append("</ol>")
        out.append("</figure>")
    return out


def _patterns(track: TalkTrack, patterns: dict[str, ArchitecturePattern]) -> list[str]:
    if not track.patterns:
        return []
    out = ['<h2 id="patterns">Architecture patterns</h2><div class="grid">']
    for pid in track.patterns:
        pat = patterns[pid]
        out.append(
            f'<div class="card"><h3>{pat.id} · {html.escape(pat.name)} {_chip(pat.status)}</h3>'
            f"<p>{_inline(pat.summary)}</p>"
            f'<p class="muted"><strong>Use when:</strong> {_inline(pat.when_to_use)}</p>'
            f'<p class="muted"><strong>Avoid when:</strong> {_inline(pat.when_not_to_use)}</p>'
            f'<p class="muted"><strong>Authority:</strong> {_inline(pat.authority)}</p></div>'
        )
    out.append("</div>")
    return out


def _step(number: int, step: Step, entry: EntryPoint) -> list[str]:
    out = [
        '<article class="step"><div class="step-h">'
        f'<span class="step-n">{number}</span><span class="step-t">{html.escape(step.title)}</span>'
        f'<span class="entry-tag">{html.escape(entry.name)}</span>{_chip(step.label)}</div>'
        f'<div class="step-b"><div class="path">{_inline(step.path)}</div>'
        '<div class="says"><span class="lbl">Say</span>'
        + "".join(f"<p>{_inline(line)}</p>" for line in step.say)
        + "</div>"
    ]
    if step.show:
        out.append('<div class="shows"><span class="lbl">Show</span><ul>')
        out += [f"<li>{_inline(s)}</li>" for s in step.show]
        out.append("</ul></div>")
    if step.code:
        out.append(f"<pre><code>{html.escape(step.code.rstrip())}</code></pre>")
    if step.check:
        out.append(
            f'<div class="chk"><span class="lbl">Checkpoint</span>{_inline(step.check)}</div>'
        )
    if step.fallback:
        out.append(
            f'<div class="fb"><span class="lbl">Fallback</span>{_inline(step.fallback)}</div>'
        )
    out.append("</div></article>")
    return out


def _parts(track: TalkTrack) -> list[str]:
    entries = {e.id: e for e in track.entry_points}
    out: list[str] = []
    number = 0
    for index, part in enumerate(track.parts):
        letter = chr(ord("A") + index)
        out.append(
            f'<section class="part-band" id="{part.id}"><h2>Part {letter} · {html.escape(part.title)}'
            f" · {part.minutes} min</h2><p>{_inline(part.goal)}</p></section>"
        )
        for step in part.steps:
            number += 1
            out += _step(number, step, entries[step.entry])
    return out


def _qa(track: TalkTrack, source_titles: dict[str, tuple[str, str]]) -> list[str]:
    if not track.qa:
        return []
    out = ['<h2 id="qa">Questions and answers</h2>']
    for qa in sorted(track.qa, key=lambda a: not a.featured):
        refs = ""
        if qa.sources:
            links = ", ".join(
                f'<a href="{html.escape(source_titles[s][1])}">{html.escape(source_titles[s][0])}</a>'
                for s in qa.sources
            )
            refs = f'<p class="muted"><strong>Sources:</strong> {links}</p>'
        css, opened = ("qa featured", " open") if qa.featured else ("qa", "")
        out.append(
            f'<details class="{css}"{opened}><summary>{html.escape(qa.q)} {_chip(qa.label)}</summary>'
            f'<div class="ans">{_blocks(qa.a)}{refs}</div></details>'
        )
    return out


def _closing(track: TalkTrack) -> list[str]:
    out: list[str] = []
    if track.options:
        out.append(
            '<h2 id="options">Options and recommendations</h2><table><thead><tr>'
            "<th>Decision</th><th>Options</th><th>Recommendation</th></tr></thead><tbody>"
        )
        out += [
            f"<tr><td>{_inline(o.decision)}</td><td>{_inline(o.options)}</td>"
            f"<td>{_inline(o.recommendation)}</td></tr>"
            for o in track.options
        ]
        out.append("</tbody></table>")
    out.append('<h2 id="reset">Reset, teardown and fallback</h2><ul>')
    out += [f"<li>{_inline(r)}</li>" for r in track.reset]
    out.append("</ul>")
    if track.mapping:
        out.append(
            "<h3>Where everything lives in the accelerator</h3><table><thead><tr><th>Need</th>"
            "<th>Asset</th></tr></thead><tbody>"
        )
        out += [
            f"<tr><td>{_inline(m.need)}</td><td>{_inline(m.asset)}</td></tr>" for m in track.mapping
        ]
        out.append("</tbody></table>")
    out.append(
        '<p class="foot">Generated by <code>ffia talktracks render</code> from '
        f"<code>demos/{track.id}/{TALK_TRACK_FILE}</code>. Edit the YAML, not this file. "
        "Synthetic data only; no customer names or identifiers. Demonstration metrics are synthetic.</p>"
    )
    return out


def render_html(
    track: TalkTrack,
    *,
    views: dict[str, DiagramView],
    patterns: dict[str, ArchitecturePattern],
    source_titles: dict[str, tuple[str, str]],
) -> str:
    """Render the talk track as one self-contained HTML document."""
    out = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{html.escape(track.title)}</title>",
        f"<style>{_css()}</style></head><body>",
        _nav(track),
        '<main class="wrap">',
        *_hero(track),
        *_overview(track),
        *_timing(track),
        *_architecture(track, views),
        *_patterns(track, patterns),
        *_parts(track),
        *_qa(track, source_titles),
        *_closing(track),
        "</main></body></html>",
    ]
    return "\n".join(out) + "\n"
