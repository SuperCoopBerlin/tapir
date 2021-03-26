from django.http import HttpResponseForbidden


class StaffCheckMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_anonymous or request.user.is_staff:
            return self.get_response(request)

        return HttpResponseForbidden("Only staff may log in at this time")
