"""HTTP adapters for patterns; domain behavior stays in services/providers."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.api.dependencies import ContainerDep
from fabric_foundry_accelerator.education.guides import GuideStep, UseCaseGuide
from fabric_foundry_accelerator.patterns.catalog import (
    SELECTION_SIGNALS,
    ArchitecturePattern,
    Recommendation,
    recommend,
)

router = APIRouter()


class RecommendRequest(BaseModel):
    """Needs from the selection vocabulary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    needs: list[str] = Field(min_length=1)
    include_preview: bool = True


@router.get("/api/v1/patterns", tags=["patterns"])
def list_patterns(container: ContainerDep) -> list[ArchitecturePattern]:
    """All architecture patterns."""
    return list(container.catalog.patterns)


class SelectionSignal(BaseModel):
    """One need from the pattern-selection vocabulary."""

    model_config = ConfigDict(frozen=True)

    id: str
    description: str


@router.get("/api/v1/patterns/signals", tags=["patterns"])
def list_selection_signals() -> list[SelectionSignal]:
    """The needs vocabulary accepted by the pattern recommender."""
    return [SelectionSignal(id=key, description=text) for key, text in SELECTION_SIGNALS.items()]


@router.get("/api/v1/patterns/{pattern_id}", tags=["patterns"])
def get_pattern(pattern_id: str, container: ContainerDep) -> ArchitecturePattern:
    """One architecture pattern."""
    return container.catalog.get(pattern_id)


@router.post("/api/v1/patterns/recommend", tags=["patterns"])
def recommend_patterns(body: RecommendRequest, container: ContainerDep) -> list[Recommendation]:
    """Rank patterns for declared needs."""
    return recommend(container.catalog, body.needs, include_preview=body.include_preview)


@router.get("/api/v1/guides", tags=["guides"])
def list_guides(container: ContainerDep) -> list[UseCaseGuide]:
    """All Use-Case Guides."""
    return list(container.guides.values())


@router.get("/api/v1/guides/{guide_id}", tags=["guides"])
def get_guide(guide_id: str, container: ContainerDep) -> UseCaseGuide:
    """One Use-Case Guide."""
    return container.guides[guide_id]


@router.get("/api/v1/guides/{guide_id}/steps/{step_id}", tags=["guides"])
def get_guide_step(guide_id: str, step_id: str, container: ContainerDep) -> GuideStep:
    """One guide step."""
    return container.guides[guide_id].step(step_id)
