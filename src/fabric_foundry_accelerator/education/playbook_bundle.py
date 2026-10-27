"""Package complete audience pages and demo handouts for offline browser delivery."""

from html import escape
from importlib.resources import files


def render_bundle(documents: dict[str, tuple[str, str]], *, audience: str) -> str:
    """Embed every document, with isolated styles and local navigation, in one HTML file."""
    assets = files("fabric_foundry_accelerator.education")
    style = assets.joinpath("playbook_bundle.css").read_text(encoding="utf-8")
    script = assets.joinpath("playbook_bundle.js").read_text(encoding="utf-8")
    navigation = "".join(
        f'<a href="#{key}" data-page="{key}"'
        f' aria-current="{"page" if key == audience else "false"}">{escape(title)}</a>'
        for key, (title, _) in documents.items()
    )
    panels = "".join(
        f'<section class="document" id="document-{key}"'
        f"{'' if key == audience else ' hidden'}>"
        f'<h2 tabindex="-1">{escape(title)}</h2>'
        f'<iframe title="{escape(title, quote=True)}" data-page="{key}"'
        f' sandbox="allow-same-origin allow-scripts allow-popups allow-popups-to-escape-sandbox"'
        f' srcdoc="{escape(content, quote=True)}"></iframe></section>'
        for key, (title, content) in documents.items()
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fabric + Foundry | {"Customer" if audience == "customer" else "SE / developer"} field guide</title>
<style>{style}</style></head><body data-audience="{audience}">
<a class="skip" href="#content">Skip to content</a>
<header><p class="eyebrow">Fabric + Foundry / Offline field guide</p>
<h1>Show and tell. Build and learn.</h1>
<p>Two audience playbooks. Two complete workshops. Interactive architecture. One portable file.</p>
<p class="notice">LOCAL reading experience. Synthetic data only. No installation, server,
sign-in or network is needed to read the embedded pages. Opening this file runs no cloud action.</p>
<details><summary>What works offline?</summary>
<p>Both playbooks, full Fabric engineering and Foundry agent workshop handouts, diagrams,
prompts, commands, Q&amp;A and every architecture view are embedded. Search and navigation run only in this browser.</p>
<p>Implementation/source references are optional online links, labeled before opening in a
new tab. They are not required to read these handouts. This file does not embed or run the
React application, Fabric notebooks or cloud services.</p></details></header>
<nav aria-label="Embedded documents">{navigation}</nav>
<aside aria-label="Search embedded content"><label for="search">Search the field guide</label>
<input id="search" type="search" placeholder="Try approval, Direct Lake or Claude" autocomplete="off">
<p id="search-status" role="status" aria-live="polite"></p>
<ul id="results"></ul></aside>
<main id="content">{panels}</main>
<noscript><p>JavaScript is disabled. All embedded documents are shown below;
search and document switching require JavaScript.</p>
<style>.document[hidden]{{display:block}}</style></noscript>
<footer>Self-contained delivery generated with make playbooks. Optional references are online;
embedded document links never require another HTML download.</footer>
<script>{script}</script></body></html>
"""
