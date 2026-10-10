"""Composition root: builds every service with explicit dependencies (no global cloud clients)."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime

from fabric_foundry_accelerator.agents.foundry import (
    FoundryAgentProvider,
    ResponsesClient,
    SdkResponsesClient,
)
from fabric_foundry_accelerator.agents.local import LocalSalesAgent
from fabric_foundry_accelerator.agents.port import AgentProvider
from fabric_foundry_accelerator.agents.routed import RoutedAgentProvider
from fabric_foundry_accelerator.audit.store import AuditStore, InMemoryAuditStore, JsonlAuditStore
from fabric_foundry_accelerator.config.bindings import (
    BindingsError,
    TenantBindings,
    bindings_path,
    load_bindings,
)
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
from fabric_foundry_accelerator.observability.logging import get_logger
from fabric_foundry_accelerator.patterns.catalog import PatternCatalog, load_catalog
from fabric_foundry_accelerator.policies.engine import (
    ToolManifest,
    WritePolicy,
    load_tool_manifest,
    load_write_policy,
)
from fabric_foundry_accelerator.providers.fabric.auth import AzureCliTokenProvider
from fabric_foundry_accelerator.providers.fabric.live import LiveFabricProvider
from fabric_foundry_accelerator.providers.fabric.local import LocalFabricProvider
from fabric_foundry_accelerator.providers.fabric.outage import SimulatedOutageFabricProvider
from fabric_foundry_accelerator.providers.fabric.port import FabricProvider
from fabric_foundry_accelerator.providers.fabric.rest import FabricRestClient
from fabric_foundry_accelerator.providers.fabric.routed import RoutedFabricProvider
from fabric_foundry_accelerator.providers.fabric.writer import FabricScopedWriter
from fabric_foundry_accelerator.research.sources import load_registry
from fabric_foundry_accelerator.services.changes import ChangeService
from fabric_foundry_accelerator.services.education import EducationService
from fabric_foundry_accelerator.services.evaluation import EvaluationService
from fabric_foundry_accelerator.services.foundry_readiness import project_endpoint
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
    agents: RoutedAgentProvider
    changes: ChangeService
    evaluation: EvaluationService
    catalog: PatternCatalog
    guides: dict[str, UseCaseGuide]
    bindings: TenantBindings | None
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


def _live_client(
    settings: Settings,
    mode: OperatingMode,
    bindings: TenantBindings | None,
    injected: FabricRestClient | None,
) -> FabricRestClient | None:
    """Return a live client only when live access is explicitly enabled and fully configured."""
    if not settings.fabric_live:
        return None
    if mode is OperatingMode.OFFLINE:
        raise BindingsError("FFIA_FABRIC_LIVE=1 needs FFIA_ENVIRONMENT=hybrid or live")
    if bindings is None:
        if mode is OperatingMode.HYBRID and not settings.allow_live_mutation:
            get_logger(__name__).warning(
                "fabric_live_not_configured",
                reason="Missing local tenant bindings; HYBRID reads use labeled LOCAL fallback.",
            )
            return None
        raise BindingsError(
            f"FFIA_FABRIC_LIVE=1 needs {bindings_path(settings.config_root, settings.overlay)} "
            "(git-ignored); copy the .local.example.yaml next to it"
        )
    return injected or FabricRestClient(AzureCliTokenProvider(bindings.tenant_id))


def _live_agent(
    settings: Settings,
    environment: EnvironmentConfiguration,
    bindings: TenantBindings | None,
    injected: ResponsesClient | None,
) -> AgentProvider | None:
    """Return a live Foundry agent provider only when explicitly enabled and fully configured."""
    if not settings.foundry_live:
        return None
    mode = environment.mode
    if mode is OperatingMode.OFFLINE:
        raise BindingsError("FFIA_FOUNDRY_LIVE=1 needs FFIA_ENVIRONMENT=hybrid or live")
    if bindings is None or bindings.foundry is None:
        if mode is OperatingMode.HYBRID and not settings.allow_live_mutation:
            get_logger(__name__).warning(
                "foundry_live_not_configured",
                reason="Missing Foundry binding; HYBRID reads use labeled LOCAL fallback.",
            )
            return None
        raise BindingsError(
            f"FFIA_FOUNDRY_LIVE=1 needs a `foundry:` section in "
            f"{bindings_path(settings.config_root, settings.overlay)} (git-ignored)"
        )
    # End the HTTP call shortly before the router gives up, so an abandoned call frees the lock.
    router_timeout = environment.policy("foundry_agent").timeout_seconds
    endpoint = project_endpoint(bindings.foundry)
    client = injected or SdkResponsesClient(
        endpoint,
        bindings.tenant_id,
        request_timeout=max(1.0, router_timeout - 10),
    )
    return FoundryAgentProvider(client, mode=mode)


def build_container(
    settings: Settings | None = None,
    *,
    audit: AuditStore | None = None,
    live_fabric: FabricProvider | None = None,
    fabric_client: FabricRestClient | None = None,
    agent_client: ResponsesClient | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    wall_clock: Callable[[], datetime] = utc_now,
) -> Container:
    """Build the container from settings and configuration files."""
    settings = settings or Settings()
    environment = load_environment(settings.config_root, settings.environment)
    overlay = load_overlay(settings.config_root, settings.overlay).with_previews(
        settings.preview_features
    )
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
    bindings = load_bindings(settings.config_root, settings.overlay, settings=settings)
    client = _live_client(settings, environment.mode, bindings, fabric_client)
    live = live_fabric or (
        SimulatedOutageFabricProvider() if settings.simulate_fabric_outage else None
    )
    if live is None and client is not None and bindings is not None:
        live = LiveFabricProvider(
            client, bindings, data_root=settings.data_root, mode=environment.mode
        )
    writer = (
        FabricScopedWriter(client, bindings, definitions_root=settings.definitions_root)
        if client is not None and bindings is not None and settings.allow_live_mutation
        else None
    )
    fabric = RoutedFabricProvider(router, local=local, live=live)
    agents = RoutedAgentProvider(
        router,
        local=LocalSalesAgent(settings.data_root, mode=local_mode),
        live=_live_agent(settings, environment, bindings, agent_client),
    )
    write_policy = load_write_policy(settings.config_root)
    changes = ChangeService(
        policy=write_policy,
        overlay=overlay,
        audit=audit,
        mode=environment.mode,
        allow_live_mutation=settings.allow_live_mutation,
        clock=wall_clock,
        live_writer=writer,
    )
    catalog = load_catalog(settings.education_root)
    guides = load_guides(settings.guides_root, catalog)
    registry = load_registry(settings.sources_path)
    library = load_education(
        settings.education_root,
        EducationReferences(
            pattern_ids=frozenset(p.id for p in catalog.patterns),
            source_ids=frozenset(s.id for s in registry.sources),
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
        agents=agents,
        changes=changes,
        evaluation=EvaluationService(
            data_root=settings.data_root,
            fabric=fabric,
            thresholds=overlay.evaluation_thresholds,
            mode=environment.mode,
        ),
        catalog=catalog,
        guides=guides,
        bindings=bindings,
        education=EducationService(library, catalog=catalog, guides=guides, registry=registry),
        built_profiles=built,
    )
