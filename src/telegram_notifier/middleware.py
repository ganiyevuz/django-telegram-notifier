from asgiref.sync import iscoroutinefunction, markcoroutinefunction

from telegram_notifier.report import report_exception


class GlobalExceptionReporterMiddleware:
    async_capable = True
    sync_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    def __call__(self, request):
        request._tn_body = getattr(request, "body", b"")
        return self.get_response(request)

    async def __acall__(self, request):
        request._tn_body = getattr(request, "body", b"")
        return await self.get_response(request)

    def process_exception(self, request, exception):
        body = getattr(request, "_tn_body", b"")
        report_exception(exception, request, body)
