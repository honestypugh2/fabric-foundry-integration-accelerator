"""``ffia talktracks render | check``: presenter talk tracks as self-contained HTML."""

import argparse
import sys
from pathlib import Path

from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.education.diagrams import load_views
from fabric_foundry_accelerator.education.guides import load_guides
from fabric_foundry_accelerator.education.talktracks import (
    HTML_FILE,
    TalkTrack,
    load_talk_tracks,
    reference_errors,
    render_html,
)
from fabric_foundry_accelerator.patterns.catalog import load_catalog
from fabric_foundry_accelerator.research.sources import load_registry


def rendered(settings: Settings) -> tuple[dict[Path, str], list[str]]:
    """Return {output path: html} for every talk track, plus reference errors."""
    catalog = load_catalog(settings.education_root)
    views = {v.id: v for v in load_views(settings.education_root / "architecture" / "views")}
    patterns = {p.id: p for p in catalog.patterns}
    registry = load_registry(settings.sources_path)
    titles = {s.id: (s.title, str(s.url)) for s in registry.sources}
    guides = frozenset(load_guides(settings.guides_root, catalog))
    outputs: dict[Path, str] = {}
    errors: list[str] = []
    tracks: dict[str, TalkTrack] = load_talk_tracks(settings.demos_root)
    for track in tracks.values():
        found = reference_errors(
            track, views=views, patterns=patterns, source_ids=frozenset(titles), guide_ids=guides
        )
        errors += found
        if not found:
            page = render_html(track, views=views, patterns=patterns, source_titles=titles)
            outputs[settings.demos_root / track.id / HTML_FILE] = page
            # The web app serves the same handout at /talktracks/<id>.html (Vite public folder).
            outputs[settings.frontend_root / "public" / "talktracks" / f"{track.id}.html"] = page
    return outputs, errors


def _cmd_render(_: argparse.Namespace) -> int:
    outputs, errors = rendered(Settings())
    for error in errors:
        sys.stderr.write(f"talktracks: {error}\n")
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        sys.stdout.write(f"wrote {path}\n")
    return 1 if errors else 0


def _cmd_check(_: argparse.Namespace) -> int:
    outputs, errors = rendered(Settings())
    for path, content in outputs.items():
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            errors.append(f"{path} is stale; run `ffia talktracks render`")
    for error in errors:
        sys.stderr.write(f"talktracks: {error}\n")
    if not errors:
        sys.stdout.write(
            f"{len(outputs)} talk-track files (handouts and app copies) are valid and up to date\n"
        )
    return 1 if errors else 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``talktracks`` subcommands."""
    parser = subparsers.add_parser("talktracks", help="presenter talk tracks (HTML handouts)")
    sub = parser.add_subparsers(dest="talktracks_command", required=True)
    sub.add_parser("render", help="render every demos/<id>/talk-track.yaml").set_defaults(
        func=_cmd_render
    )
    sub.add_parser("check", help="validate references and fail when HTML is stale").set_defaults(
        func=_cmd_check
    )
