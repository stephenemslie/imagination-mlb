METHOD_OVERRIDE_HEADER = 'HTTP_X_HTTP_METHOD_OVERRIDE'


class MethodOverrideMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST' and request.META.get(METHOD_OVERRIDE_HEADER):
            request.method = request.META[METHOD_OVERRIDE_HEADER]
        return self.get_response(request)
