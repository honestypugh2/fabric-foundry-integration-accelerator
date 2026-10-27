"""HTTP adapters for bakeoff; domain behavior stays in services/providers."""

from fastapi import APIRouter

from fabric_foundry_accelerator.api.dependencies import ContainerDep
from fabric_foundry_accelerator.bakeoff.runs import (
    REPLAYS_DIR,
    RunRecord,
    Scorecard,
    get_run,
    load_runs,
    scorecard,
)
from fabric_foundry_accelerator.bakeoff.tasks import TaskSet, load_tasks

router = APIRouter()


@router.get("/api/v1/bakeoff/tasks", tags=["bakeoff"])
def bakeoff_tasks(container: ContainerDep) -> TaskSet:
    """The bake-off tasks with their exact prompts and checks."""
    return load_tasks(container.settings.config_root)


@router.get("/api/v1/bakeoff/scorecard", tags=["bakeoff"])
def bakeoff_scorecard(container: ContainerDep) -> Scorecard:
    """Recorded runs and per-harness, per-model aggregates (UNAVAILABLE when none)."""
    settings = container.settings
    return scorecard(load_tasks(settings.config_root), load_runs(settings.demos_root / REPLAYS_DIR))


@router.get("/api/v1/bakeoff/runs/{run_id}", tags=["bakeoff"])
def bakeoff_run(run_id: str, container: ContainerDep) -> RunRecord:
    """One recorded run with its sanitized transcript."""
    return get_run(container.settings.demos_root / REPLAYS_DIR, run_id)
