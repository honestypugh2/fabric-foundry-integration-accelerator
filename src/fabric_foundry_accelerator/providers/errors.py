"""Errors raised by providers. API layers translate these into user-facing responses."""


class ProviderError(RuntimeError):
    """Base class for provider errors."""


class UnknownResourceError(ProviderError, LookupError):
    """Raised when a workspace, item, table or measure is not in the provider's catalog."""


class InvalidRequestError(ProviderError, ValueError):
    """Raised when request arguments are outside the allowed contract (e.g., limits)."""
