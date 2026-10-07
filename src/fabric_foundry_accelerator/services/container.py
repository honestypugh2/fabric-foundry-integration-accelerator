"""Composition root: builds every service with explicit dependencies (no global cloud clients)."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime

from fabric_foundry_accelerator.audit.store import AuditStore, InMemoryAuditStore, JsonlAuditStore
from fabric_foundry_accelerator.config.environment import EnvironmentConfiguration, load_environment
from fabric_foundry_accelerator.config.overlay import CustomerOverlay, load_overlay
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.education.guides import UseCaseGuide, load_guides
from fabric_foundry_accelerator.education.lessons import (
    EducationReferences,
    guide_diagram_errors,
    load_education,
)
from fabric_foundry_accelerator.fallback.router import ProviderRouter
from fabric_foundry_accelerator.models.execution import OperatingMode, utc_now
from fabric_foundry_accelerator.models.semantic import load_semantic_model
from fabric_foundry_accelerator.patterns.catalog import PatternCatalog, load_catalog
from fabric_foundry_accelerator.policies.engine import (
    ToolManifest,
    WritePolicy,
    load_tool_manifest,
    load_write_policy,
)
from fabric_foundry_accelerator.providers.fabric.local import LocalFabricProvider
from fabric_foundry_accelerator.providers.fabric.outage import SimulatedOutageFabricProvider
from fabric_foundry_accelerator.providers.fabric.port import FabricProvider
from fabric_foundry_accelerator.providers.fabric.routed import RoutedFabricProvider
from fabric_foundry_accelerator.research.sources import load_registry
from fabric_foundry_accelerator.services.changes import ChangeService
from fabric_foundry_accelerator.services.education import EducationService
from fabric_foundry_accelerator.services.evaluation import EvaluationService
from fabric_foundry_accelerator.synthetic.medallion import build_profile, lakehouse_tables
from fabric_foundry_accelerator.synthetic.paths import raw_dir, semantic_model_path
from fabric_foundry_accelerator.synthetic.profiles import PROFILES


@dataclass(slots=True)
class Container:
    """All services for one process (API server, MCP server, CLI demo)."""

    settings: Settings
    environment: EnvironmentConfiguration
    overlay: CustomerOverlay
    write_policy: WritePolicy
    tool_manifest: ToolManifest
    audit: AuditStore
    router: ProviderRouter
    local_fabric: LocalFabricProvider
    fabric: RoutedFabricProvider
    changes: ChangeService
    evaluation: EvaluationService
    catalog: PatternCatalog
    guides: dict[str, UseCaseGuide]
    education: EducationService
    built_profiles: list[str] = field(default_factory=list[str])

    @property
    def mode(self) -> OperatingMode:
        """Return the operating mode."""
        return self.environment.mode


def ensure_data_built(settings: Settings) -> list[str]:
    """Build any profile whose local lakehouse is missing; return the profiles that were built."""
    built: list[str] = []
    for profile in PROFILES.values():
        if lakehouse_tables(settings.lakehouse_root, profile.id):
            continue
        model = load_semantic_model(semantic_model_path(settings.data_root, profile.id))
        build_profile(
            profile,
            raw_dir=raw_dir(settings.data_root, profile.id),
            output_root=settings.lakehouse_root,
            semantic_model=model,
        )
        built.append(profile.id)
    return built


def build_container(
    settings: Settings | None = None,
    *,
    audit: AuditStore | None = None,
    live_fabric: FabricProvider | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    wall_clock: Callable[[], datetime] = utc_now,
) -> Container:
    """Build the container from settings and configuration files."""
    settings = settings or Settings()
    environment = load_environment(settings.config_root, settings.environment)
    overlay = load_overlay(settings.config_root, settings.overlay)
    built = ensure_data_built(settings) if settings.auto_build_data else []
    if audit is None:
        audit = (
            JsonlAuditStore(settings.audit_path) if settings.audit_path else InMemoryAuditStore()
        )
    router = ProviderRouter(environment, audit=audit, clock=clock, sleep=sleep)
    local_mode = (
        OperatingMode.OFFLINE if environment.mode is OperatingMode.OFFLINE else OperatingMode.HYBRID
    )
    local = LocalFabricProvider(
        settings.data_root, output_root=settings.lakehouse_root, mode=local_mode
    )
    live = live_fabric or (
        SimulatedOutageFabricProvider() if settings.simulate_fabric_outage else None
    )
    fabric = RoutedFabricProvider(router, local=local, live=live)
    write_policy = load_write_policy(settings.config_root)
    changes = ChangeService(
        policy=write_policy,
        overlay=overlay,
        audit=audit,
        mode=environment.mode,
        allow_live_mutation=settings.allow_live_mutation,
        clock=wall_clock,
    )
    catalog = load_catalog(settings.education_root)
    guides = load_guides(settings.guides_root, catalog)
    library = load_education(
        settings.education_root,
        EducationReferences(
            pattern_ids=frozenset(p.id for p in catalog.patterns),
            source_ids=frozenset(s.id for s in load_registry(settings.sources_path).sources),
            guide_ids=frozenset(guides),
        ),
    )
    diagram_errors = guide_diagram_errors(library, guides)
    if diagram_errors:
        raise ValueError("guide diagrams are invalid:\n- " + "\n- ".join(diagram_errors))
    return Container(
        settings=settings,
        environment=environment,
        overlay=overlay,
        write_policy=write_policy,
        tool_manifest=load_tool_manifest(settings.config_root),
        audit=audit,
        router=router,
        local_fabric=local,
        fabric=fabric,
        changes=changes,
        evaluation=EvaluationService(
            data_root=settings.data_root,
            fabric=fabric,
            thresholds=overlay.evaluation_thresholds,
            mode=environment.mode,
        ),
        catalog=catalog,
        guides=guides,
        education=EducationService(library),
        built_profiles=built,
    )
