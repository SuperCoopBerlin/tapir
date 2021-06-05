from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from tapir.log.models import EmailLogEntry
from tapir.log.util import freeze_for_log


@require_GET
@permission_required("coop.manage")
def email_log_entry_content(request, pk):
    log_entry = get_object_or_404(EmailLogEntry, pk=pk)
    filename = "tapir_email_{}_{}.eml".format(
        log_entry.user.username, log_entry.created_date.strftime("%Y-%m-%d_%H-%M-%S")
    )

    response = HttpResponse(content_type="application/octet-stream")
    response["Content-Disposition"] = 'filename="{}"'.format(filename)
    response.write(log_entry.email_content)
    return response


class UpdateViewLogMixin:
    def get_object(self, *args, **kwargs):
        result = super().get_object(*args, **kwargs)
        self.old_object_frozen = freeze_for_log(result)
        return result
