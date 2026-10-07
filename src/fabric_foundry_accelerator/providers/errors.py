"""Errors raised by providers. API layers translate these into user-facing responses."""


class ProviderError(RuntimeError):
    """Base class for provider errors."""


class UnknownResourceError(ProviderError, LookupError):
    """Raised when a workspace, item, table or measure is not in the provider's catalog."""


class InvalidRequestError(ProviderError, ValueError):
    """Raised when request arguments are outside the allowed contract (e.g., limits)."""


class ProviderUnavailableError(ProviderError):
    """Raised when a provider cannot serve a request (outage, timeout, not configured)."""


CLIENT_ERRORS: tuple[type[ProviderError], ...] = (UnknownResourceError, InvalidRequestError)
"""Errors caused by the request itself. They never trigger retries, breakers or fallback."""
