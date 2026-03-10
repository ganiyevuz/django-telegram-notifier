SENSITIVE_HEADERS = {"Authorization", "Cookie", "Set-Cookie", "X-Csrftoken"}


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_filtered_headers(request):
    headers = {}
    for key, value in request.META.items():
        if key.startswith("HTTP_"):
            header_name = key[5:].replace("_", "-").title()
            if header_name not in SENSITIVE_HEADERS:
                headers[header_name] = value
    return headers


def get_view_name(request):
    if hasattr(request, "resolver_match") and request.resolver_match:
        return request.resolver_match.view_name or ""
    return ""
