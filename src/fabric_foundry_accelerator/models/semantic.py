"""Semantic model contract: entities, relationships, measures and business vocabulary.

This is the local analog of a Power BI semantic model plus Fabric IQ-style business
vocabulary. The same definitions drive local measure evaluation (DuckDB SQL), the
reference DAX for the live Direct Lake model, and AI-readiness descriptions.
"""

import re
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

_IDENT = r"^[a-z_][a-z0-9_]*$"
_IDENT_RE = re.compile(_IDENT)


class SemanticTable(BaseModel):
    """A table included in the semantic model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(pattern=_IDENT)
    role: Literal["fact", "dimension"]
    grain: str
    description: str
    key: str | None = Field(default=None, pattern=_IDENT)
    synonyms: tuple[str, ...] = ()


class ExcludedItem(BaseModel):
    """A table or measure deliberately left out, with the reason recorded."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    reason: str


class SemanticRelationship(BaseModel):
    """A one-to-many, single-direction relationship from a dimension to a fact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    from_table: str = Field(pattern=_IDENT)
    from_column: str = Field(pattern=_IDENT)
    to_table: str = Field(pattern=_IDENT)
    to_column: str = Field(pattern=_IDENT)
    cardinality: Literal["one_to_many"] = "one_to_many"
    cross_filter: Literal["single"] = "single"
    active: bool = True
    role: str | None = None
    description: str


class SemanticMeasure(BaseModel):
    """A measure contract with its local SQL and reference DAX."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(pattern=_IDENT)
    display_name: str
    home_table: str = Field(pattern=_IDENT)
    description: str
    definition: str
    format: Literal["integer", "decimal", "percent", "currency"]
    sql: str
    dax: str
    dax_validated: bool = False
    zero_denominator: str = "Returns blank (null) when the denominator is zero."
    synthetic_demonstration: bool = False

    @model_validator(mode="after")
    def _sql_is_single_select(self) -> Self:
        text = self.sql.strip()
        if not text.upper().startswith(("SELECT", "WITH")) or ";" in text:
            raise ValueError(f"measure {self.name}: sql must be a single SELECT statement")
        return self


class VocabularyTerm(BaseModel):
    """A business term with its definition and synonyms (AI readiness)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    term: str
    definition: str
    synonyms: tuple[str, ...] = ()


class SemanticModel(BaseModel):
    """The full semantic model for one dataset profile."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    profile: str
    name: str
    description: str
    synthetic_notice: str
    storage_mode: Literal["DirectLake", "Import", "DirectQuery"]
    tables: tuple[SemanticTable, ...]
    excluded_tables: tuple[ExcludedItem, ...] = ()
    relationships: tuple[SemanticRelationship, ...]
    measures: tuple[SemanticMeasure, ...]
    excluded_measures: tuple[ExcludedItem, ...] = ()
    vocabulary: tuple[VocabularyTerm, ...] = ()

    @model_validator(mode="after")
    def _check_references(self) -> Self:
        names = {t.name for t in self.tables}
        if len(names) != len(self.tables):
            raise ValueError("duplicate table names")
        roles = {t.name: t.role for t in self.tables}
        for rel in self.relationships:
            if rel.from_table not in names or rel.to_table not in names:
                raise ValueError(f"relationship references unknown table: {rel}")
            if roles[rel.from_table] != "dimension" or roles[rel.to_table] != "fact":
                raise ValueError("relationships must run from a dimension to a fact")
        measure_names = [m.name for m in self.measures]
        if len(set(measure_names)) != len(measure_names):
            raise ValueError("duplicate measure names")
        for measure in self.measures:
            if measure.home_table not in names:
                raise ValueError(f"measure {measure.name} has unknown home table")
        return self

    def measure(self, name: str) -> SemanticMeasure:
        """Return a measure by name or raise ``KeyError``."""
        for candidate in self.measures:
            if candidate.name == name:
                return candidate
        raise KeyError(name)


def is_identifier(name: str) -> bool:
    """Return True when ``name`` is a safe lowercase SQL identifier."""
    return bool(_IDENT_RE.match(name))


def load_semantic_model(path: Path) -> SemanticModel:
    """Load and validate a semantic model YAML file."""
    return SemanticModel.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
