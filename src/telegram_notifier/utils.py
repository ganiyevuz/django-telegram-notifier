SENSITIVE_HEADERS = frozenset({
    "Authorization",
    "Cookie",
    "Set-Cookie",
    "X-Api-Key",
    "X-Csrftoken",
})

HTTP_PREFIX = "HTTP_"
HTTP_PREFIX_LEN = len(HTTP_PREFIX)


def _get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        ip = forwarded.split(",", 1)[0].strip()
        if _is_valid_ip(ip):
            return ip
        return None
    return request.META.get("REMOTE_ADDR")


def _is_valid_ip(value):
    import ipaddress

    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _get_filtered_headers(request):
    headers = {}
    for key, value in request.META.items():
        if key.startswith(HTTP_PREFIX):
            header_name = key[HTTP_PREFIX_LEN:].replace("_", "-").title()
            if header_name not in SENSITIVE_HEADERS:
                headers[header_name] = value
    return headers


def _get_view_name(request):
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match:
        return resolver_match.view_name or ""
    return ""
