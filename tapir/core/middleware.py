import logging
import traceback
from itertools import chain

import requests
from django.http import HttpRequest
from icecream import ic

from tapir import settings

LOG = logging.getLogger(__name__)


class SendExceptionsToSlackMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        try:
            response = self.get_response(request)
        except Exception as e:
            stacktrace_string = traceback.format_exc()
            self.send_slack_message(e, stacktrace_string, request, source="Try/Catch")
            raise e
        return response

    def process_exception(self, request: HttpRequest, exception):
        stacktrace_string = traceback.format_exc()
        self.send_slack_message(
            exception, stacktrace_string, request, source="Process exception"
        )
        return None

    @classmethod
    def send_slack_message(
        cls, e: Exception, stacktrace_string: str, request: HttpRequest, source: str
    ):
        error_text = f"{e}"
        if not error_text:
            error_text = "Could not get exception text"

        if not stacktrace_string:
            stacktrace_string = "No stacktrace available"

        sections = [
            cls.build_section(
                "Hi @channel! The following error happened on the production server :ladybug:",
                is_markdown=True,
            ),
            cls.build_section(f"Source: {source}"),
            cls.build_section(f"Request: {request}"),
            cls.build_section(f"User: {request.user}"),
            cls.build_section(f"Request headers: {request.headers}"),
            cls.build_section(
                f"Request Body: {request.body.decode() if not request._read_started else 'Cannot access body'}"
            ),
            cls.build_section(f"Error: {error_text}", is_markdown=True),
            cls.build_section(stacktrace_string),
        ]
        sections_and_dividers = list(
            chain.from_iterable(({"type": "divider"}, section) for section in sections)
        )

        data = {
            "channel": "C079AQN3HE2",
            "blocks": sections_and_dividers,
        }

        if settings.DEBUG:
            ic(data)
            return

        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Content-type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",
        }
        response = requests.post(url, json=data, headers=headers)
        if not response.json().get("ok", False):
            LOG.error(
                f"Failed to send slack message. Response from slack: {response.text}"
            )

    @staticmethod
    def build_section(text: str, is_markdown=False):
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn" if is_markdown else "plain_text",
                "text": text,
            },
        }
