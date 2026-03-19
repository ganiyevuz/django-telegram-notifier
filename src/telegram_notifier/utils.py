from __future__ import annotations

import ipaddress

from django.http import HttpRequest

from telegram_notifier.choices import Level, Severity

SENSITIVE_HEADERS: frozenset[str] = frozenset(
    {
        "Authorization",
        "Cookie",
        "Set-Cookie",
        "X-Api-Key",
        "X-Csrftoken",
    }
)

HTTP_PREFIX = "HTTP_"
HTTP_PREFIX_LEN = len(HTTP_PREFIX)


def _get_client_ip(request: HttpRequest) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        ip = forwarded.split(",", 1)[0].strip()
        if _is_valid_ip(ip):
            return ip
        return None
    return request.META.get("REMOTE_ADDR")


def _is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _get_filtered_headers(request: HttpRequest) -> dict[str, str]:
    headers: dict[str, str] = {}
    for key, value in request.META.items():
        if key.startswith(HTTP_PREFIX):
            header_name = key[HTTP_PREFIX_LEN:].replace("_", "-").title()
            if header_name not in SENSITIVE_HEADERS:
                headers[header_name] = value
    return headers


def _get_view_name(request: HttpRequest) -> str:
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match:
        return resolver_match.view_name or ""
    return ""


# --- Exception classification ---

# Critical: system-level failures that need immediate attention
_CRITICAL_EXCEPTIONS: tuple[str, ...] = (
    "SystemExit",
    "MemoryError",
    "RecursionError",
    "SystemError",
)

# Warning: expected client/validation errors, not bugs
_WARNING_EXCEPTIONS: tuple[str, ...] = (
    "Http404",
    "PermissionDenied",
    "ValidationError",
    "SuspiciousOperation",
    "BadRequest",
    "DisallowedHost",
    "DisallowedRedirect",
    "RequestDataTooBig",
    "TooManyFieldsSent",
    "AuthenticationFailed",
    "NotAuthenticated",
    "Throttled",
    "MethodNotAllowed",
    "NotAcceptable",
    "UnsupportedMediaType",
    "ParseError",
)

# High severity: infrastructure/data failures
_HIGH_SEVERITY_EXCEPTIONS: tuple[str, ...] = (
    "DatabaseError",
    "OperationalError",
    "IntegrityError",
    "ConnectionError",
    "ConnectionRefusedError",
    "ConnectionResetError",
    "TimeoutError",
    "OSError",
    "IOError",
    "PermissionError",
    "FileNotFoundError",
)


def classify_exception(
    exc: BaseException,
) -> tuple[str, str]:
    """Return (level, severity) for an exception.

    Walks the MRO so subclasses of known types are classified
    correctly (e.g. IntegrityError inherits DatabaseError).
    """
    names = {cls.__name__ for cls in type(exc).__mro__}

    # Critical system errors
    if names & set(_CRITICAL_EXCEPTIONS):
        return Level.CRITICAL, Severity.CRITICAL

    # Client/validation errors → warning + low/moderate
    if names & set(_WARNING_EXCEPTIONS):
        return Level.WARNING, Severity.LOW

    # Infrastructure errors → error + high
    if names & set(_HIGH_SEVERITY_EXCEPTIONS):
        return Level.ERROR, Severity.HIGH

    # Default: error + moderate
    return Level.ERROR, Severity.MODERATE
