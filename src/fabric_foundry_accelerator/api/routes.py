"""Compose feature routers without owning domain logic or request contracts."""

from fastapi import APIRouter

from fabric_foundry_accelerator.api.routers import (
    agents,
    bakeoff,
    changes,
    education,
    fabric,
    operations,
    patterns,
    runtime,
)

router = APIRouter()

router.include_router(runtime.router)
router.include_router(patterns.router)
router.include_router(fabric.router)
router.include_router(agents.router)
router.include_router(bakeoff.router)
router.include_router(changes.router)
router.include_router(operations.router)
router.include_router(education.router)
