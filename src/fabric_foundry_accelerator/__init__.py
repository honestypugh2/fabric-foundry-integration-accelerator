"""Fabric Foundry Integration Accelerator.

Fabric provides governed business context. Foundry turns that context into
reasoning, orchestration, evaluation, and action. MCP standardizes capability
access; identity and policy provide authority.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fabric-foundry-accelerator")
except PackageNotFoundError:  # pragma: no cover - only when running from an uninstalled tree
    __version__ = "0.0.0"

__all__ = ["__version__"]
