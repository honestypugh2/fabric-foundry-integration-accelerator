"""HTTP adapters for education; domain behavior stays in services/providers."""

from fastapi import APIRouter, Response
from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.api.dependencies import ContainerDep
from fabric_foundry_accelerator.education.diagrams import DiagramView
from fabric_foundry_accelerator.education.drawio import render_drawio
from fabric_foundry_accelerator.education.layout import ViewLayout, compute_layout
from fabric_foundry_accelerator.education.lessons import ArchitectureMap, CompletenessReport, Lab
from fabric_foundry_accelerator.services.diagram_runtime import ViewRuntime, view_runtime
from fabric_foundry_accelerator.services.education import (
    CheckAnswer,
    CheckGrade,
    LabSummary,
    LessonSummary,
    LessonView,
    WorkshopView,
)

router = APIRouter()


@router.get("/api/v1/education/workshop", tags=["education"])
def get_workshop(container: ContainerDep) -> WorkshopView:
    """LOCAL instructional journeys, reading references and pattern coverage."""
    return container.education.workshop()


@router.get("/api/v1/education/lessons", tags=["education"])
def list_lessons(
    container: ContainerDep, area: str | None = None, pattern_id: str | None = None
) -> list[LessonSummary]:
    """Lesson summaries, optionally filtered by area or pattern."""
    return container.education.lessons(area=area, pattern_id=pattern_id)


@router.get("/api/v1/education/lessons/{lesson_id}", tags=["education"])
def get_lesson(lesson_id: str, container: ContainerDep) -> LessonView:
    """One lesson with all five levels and its knowledge checks (answers withheld)."""
    return container.education.lesson(lesson_id)


@router.post("/api/v1/education/lessons/{lesson_id}/checks/{check_id}", tags=["education"])
def answer_check(
    lesson_id: str, check_id: str, body: CheckAnswer, container: ContainerDep
) -> CheckGrade:
    """Grade one knowledge-check answer."""
    return container.education.grade(lesson_id, check_id, body)


@router.get("/api/v1/education/labs", tags=["education"])
def list_labs(container: ContainerDep) -> list[LabSummary]:
    """Lab summaries."""
    return container.education.labs()


@router.get("/api/v1/education/labs/{lab_id}", tags=["education"])
def get_lab(lab_id: str, container: ContainerDep) -> Lab:
    """One lab with its eleven stages."""
    return container.education.lab(lab_id)


@router.get("/api/v1/education/architecture", tags=["education"])
def get_architecture(container: ContainerDep) -> ArchitectureMap:
    """The architecture explorer map."""
    return container.education.library.architecture


@router.get("/api/v1/education/completeness", tags=["education"])
def get_completeness(container: ContainerDep) -> CompletenessReport:
    """Coverage of the 30-question architecture completeness gate."""
    return container.education.library.completeness_report()


class ViewSummary(BaseModel):
    """An architecture view in a list."""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    kind: str
    summary: str
    doc: str | None
    pattern_ids: tuple[str, ...]


@router.get("/api/v1/education/views", tags=["education"])
def list_views(container: ContainerDep) -> list[ViewSummary]:
    """Architecture views (interactive diagrams)."""
    return [
        ViewSummary(
            id=v.id,
            title=v.title,
            kind=v.kind,
            summary=v.summary,
            doc=v.doc,
            pattern_ids=v.pattern_ids,
        )
        for v in container.education.library.views
    ]


class RenderedView(BaseModel):
    """A view with the shared layout used by both the app and the draw.io files."""

    model_config = ConfigDict(frozen=True)

    view: DiagramView
    layout: ViewLayout


@router.get("/api/v1/education/views/{view_id}", tags=["education"])
def get_view(view_id: str, container: ContainerDep) -> RenderedView:
    """One architecture view and its layout: nodes, edges, zones, bands, build steps and traces."""
    view = container.education.library.view(view_id)
    return RenderedView(view=view, layout=compute_layout(view))


@router.get("/api/v1/education/views/{view_id}/drawio", tags=["education"])
def get_view_drawio(view_id: str, container: ContainerDep) -> Response:
    """The view as a draw.io file (same content as docs/architecture/diagrams)."""
    view = container.education.library.view(view_id)
    return Response(
        content=render_drawio(view),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{view.id}.drawio"'},
    )


@router.get("/api/v1/education/views/{view_id}/runtime", tags=["education"])
def get_view_runtime(view_id: str, container: ContainerDep) -> ViewRuntime:
    """The live state of every runtime-bound node in a view."""
    return view_runtime(container, container.education.library.view(view_id))
