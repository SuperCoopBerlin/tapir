import datetime

from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.encoding import iri_to_uri
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme


def safe_redirect(redirect_url, default, request):
    if redirect_url is None:
        return redirect(default)

    if not url_has_allowed_host_and_scheme(
        url=redirect_url, allowed_hosts=None, require_https=request.is_secure()
    ):
        return redirect("/")

    url = iri_to_uri(redirect_url)
    return redirect(url)


def get_monday(date: datetime.date):
    return date - datetime.timedelta(days=date.weekday())


def get_first_of_next_month(date: datetime.date):
    return (date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)


def get_first_of_previous_first_day_of_month(date: datetime.date):
    if date.day != 1:
        return date.replace(day=1)
    return (date - datetime.timedelta(days=2)).replace(day=1)


def set_header_for_file_download(response: HttpResponse, filename: str):
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)


def get_html_link(url: str, text: str):
    return format_html("<a href={}>{}</a>", url, text)
