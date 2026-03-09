from django.utils.deprecation import MiddlewareMixin

from telegram_notifier.report import report_exception


class GlobalExceptionReporterMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self._body = None

    def process_request(self, request):
        self._body = getattr(request, "body", b"")

    def process_exception(self, request, exception):
        report_exception(exception, request, self._body)
