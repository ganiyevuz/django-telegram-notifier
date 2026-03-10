from telegram_notifier.report import report_exception


class GlobalExceptionReporterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self._body = getattr(request, "body", b"")
        return self.get_response(request)

    def process_exception(self, request, exception):
        report_exception(exception, request, self._body)
