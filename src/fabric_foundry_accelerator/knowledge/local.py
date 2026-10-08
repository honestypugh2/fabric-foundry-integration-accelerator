"""Foundry IQ knowledge retrieval, simulated offline behind a preview flag.

Foundry IQ knowledge bases (PREVIEW in parts) retrieve passages from sources such as OneLake and
cite them. This module is the offline teaching analog: deterministic keyword scoring over
synthetic Markdown policy documents, split by section, with a citation for every passage.

* Flag off (the default): the result is UNAVAILABLE and says how to enable it.
* Flag on: the result is SIMULATED with a notice. No Foundry, Azure AI Search or OneLake call is
  made, and nothing is presented as Foundry.

Retrieved text answers "what is the policy" questions. Numbers still come from the governed sales
model, never from documents.
"""

import math
import re
from collections import Counter
from pathlib import Path
from typing import cast

import yaml
from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.models.execution import (
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
    new_correlation_id,
)
from fabric_foundry_accelerator.providers.errors import ProviderUnavailableError

PREVIEW_FLAG = "foundry_iq_knowledge"
KNOWLEDGE_BASE = "mfg-sales-v1"
PROVIDER_NAME = "Local knowledge retriever (keyword scoring, synthetic documents)"
EQUIVALENT = "Foundry IQ knowledge base (Azure AI Search agentic retrieval over OneLake files)"
OBJECTIVE = "Documents answer policy questions with citations; numbers come from governed data."
NOTICE = (
    "SIMULATED Foundry IQ retrieval (PREVIEW feature) over synthetic documents with local keyword "
    "scoring. No Foundry, Azure AI Search or OneLake call was made."
)
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "its",
        "may",
        "of",
        "on",
        "or",
        "our",
        "the",
        "to",
        "we",
        "what",
        "when",
        "which",
        "who",
        "why",
        "with",
    }
)
_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


class KnowledgeQuery(BaseModel):
    """A question for the knowledge base."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    question: str = Field(min_length=3, max_length=500)
    top: int = Field(default=3, ge=1, le=5)


class Citation(BaseModel):
    """Where a passage came from."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document: str
    title: str
    section: str
    path: str


class Passage(BaseModel):
    """One retrieved section and its score."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    score: float
    citation: Citation


class KnowledgeResult(BaseModel):
    """Passages for a question, or why retrieval is unavailable."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    knowledge_base: str
    question: str
    preview_flag: str
    enabled: bool
    passages: tuple[Passage, ...]
    note: str


def _terms(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS]


def load_sections(root: Path) -> list[tuple[Citation, str]]:
    """Every ``##`` section of every document under ``root``, with its citation.

    Raises:
        ProviderUnavailableError: the knowledge folder is missing or empty.
    """
    files = sorted(root.glob("*.md")) if root.is_dir() else []
    if not files:
        raise ProviderUnavailableError(f"no knowledge documents under {root}")
    sections: list[tuple[Citation, str]] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        match = _FRONT_MATTER.match(text)
        meta: object = yaml.safe_load(match.group(1)) if match else None
        title = path.stem
        if isinstance(meta, dict):
            title = str(cast("dict[str, object]", meta).get("title", path.stem))
        body = text[match.end() :] if match else text
        for chunk in re.split(r"^## ", body, flags=re.M)[1:]:
            heading, _, content = chunk.partition("\n")
            sections.append(
                (
                    Citation(
                        document=path.stem,
                        title=title,
                        section=heading.strip(),
                        path=path.as_posix(),
                    ),
                    " ".join(content.split()),
                )
            )
    return sections


def retrieve(sections: list[tuple[Citation, str]], question: str, top: int) -> tuple[Passage, ...]:
    """Rank sections by TF-IDF over the question's terms; ties break by document and section."""
    query = set(_terms(question))
    if not query:
        return ()
    bags = [Counter(_terms(f"{c.title} {c.section} {text}")) for c, text in sections]
    df = Counter(term for bag in bags for term in set(bag) if term in query)
    scored: list[Passage] = []
    for (citation, text), bag in zip(sections, bags, strict=True):
        score = sum(
            (1 + math.log(bag[t])) * math.log(1 + len(bags) / df[t]) for t in query if bag[t]
        )
        if score > 0:
            scored.append(Passage(text=text, score=round(score, 4), citation=citation))
    scored.sort(key=lambda p: (-p.score, p.citation.document, p.citation.section))
    return tuple(scored[:top])


def search_knowledge(
    query: KnowledgeQuery,
    *,
    data_root: Path,
    enabled: bool,
    mode: OperatingMode,
    correlation_id: str | None = None,
) -> ExecutionEnvelope[KnowledgeResult]:
    """Retrieve cited passages when the preview flag is on; otherwise report UNAVAILABLE."""
    correlation_id = correlation_id or new_correlation_id()
    if not enabled:
        return ExecutionEnvelope[KnowledgeResult](
            operating_mode=mode,
            execution_label=ExecutionLabel.UNAVAILABLE,
            requested_provider=EQUIVALENT,
            selected_provider="none",
            cloud_operation_performed=False,
            equivalent_fabric_service=EQUIVALENT,
            teaching_objective=OBJECTIVE,
            data=KnowledgeResult(
                knowledge_base=KNOWLEDGE_BASE,
                question=query.question,
                preview_flag=PREVIEW_FLAG,
                enabled=False,
                passages=(),
                note=(
                    f"Foundry IQ is a preview feature and the flag {PREVIEW_FLAG} is off. Enable the "
                    f"offline simulation with FFIA_PREVIEW_FEATURES={PREVIEW_FLAG}."
                ),
            ),
            correlation_id=correlation_id,
        )
    passages = retrieve(
        load_sections(data_root / "knowledge" / KNOWLEDGE_BASE), query.question, query.top
    )
    return ExecutionEnvelope[KnowledgeResult](
        operating_mode=mode,
        execution_label=ExecutionLabel.SIMULATED,
        requested_provider=EQUIVALENT,
        selected_provider=PROVIDER_NAME,
        cloud_operation_performed=False,
        equivalent_fabric_service=EQUIVALENT,
        teaching_objective=OBJECTIVE,
        simulation_notice=NOTICE,
        data=KnowledgeResult(
            knowledge_base=KNOWLEDGE_BASE,
            question=query.question,
            preview_flag=PREVIEW_FLAG,
            enabled=True,
            passages=passages,
            note=(
                "Cite the passages; answer numeric questions from the governed sales model."
                if passages
                else "No passage matched. The knowledge base does not cover this question."
            ),
        ),
        correlation_id=correlation_id,
    )
