SENSITIVE_HEADERS = frozenset({
    "Authorization",
    "Cookie",
    "Set-Cookie",
    "X-Api-Key",
    "X-Csrftoken",
})

HTTP_PREFIX = "HTTP_"
HTTP_PREFIX_LEN = len(HTTP_PREFIX)


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_filtered_headers(request):
    headers = {}
    for key, value in request.META.items():
        if key.startswith(HTTP_PREFIX):
            header_name = key[HTTP_PREFIX_LEN:].replace("_", "-").title()
            if header_name not in SENSITIVE_HEADERS:
                headers[header_name] = value
    return headers


def get_view_name(request):
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match:
        return resolver_match.view_name or ""
    return ""
