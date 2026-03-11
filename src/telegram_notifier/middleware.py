from __future__ import annotations

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http import HttpRequest, HttpResponse

from telegram_notifier.report import report_exception


class GlobalExceptionReporterMiddleware:
    async_capable = True
    sync_capable = True

    def __init__(self, get_response: callable) -> None:
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request._tn_body = getattr(request, "body", b"")  # type: ignore[attr-defined]
        return self.get_response(request)

    async def __acall__(self, request: HttpRequest) -> HttpResponse:
        request._tn_body = getattr(request, "body", b"")  # type: ignore[attr-defined]
        return await self.get_response(request)

    def process_exception(
        self,
        request: HttpRequest,
        exception: BaseException,
    ) -> None:
        body: bytes = getattr(request, "_tn_body", b"")
        report_exception(exception, request, body)
