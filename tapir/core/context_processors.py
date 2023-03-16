from django.conf import settings


def settings_context_processor(request):
    # TODO: Make it more secure only accessing certain settings which are
    # considered safe, e.g. `return {'settings': settings.TAPIR}`.
    # The environment variables would have to be be adapted accordingly, but
    # this way we could avoid exposing things like `settings.DATABASES` by
    # mistake while still having a generic one-liner to access tapir settings.
    return {"settings": settings}
