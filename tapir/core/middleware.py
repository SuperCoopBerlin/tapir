import logging
import traceback
from itertools import chain

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

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
        if settings.DEBUG:
            return

        if isinstance(e, PermissionDenied):
            # PermissionDenied errors are not sent to slack because
            # they show up even when the member actually has the required permissions.
            # I couldn't figure out the reasons for it, but we need to reduce the spam in the channel.
            return

        client = WebClient(token=settings.SLACK_BOT_TOKEN)

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
        ]
        sections_and_dividers = list(
            chain.from_iterable(({"type": "divider"}, section) for section in sections)
        )

        data = {
            "channel": "C079AQN3HE2",
            "blocks": sections_and_dividers,
        }

        try:
            client.chat_postMessage(channel="C079AQN3HE2", blocks=sections_and_dividers)
        except SlackApiError as e:
            LOG.error(
                f"Failed to send slack message. Response from slack: {e.response["error"]}"
            )
            return

        try:
            client.files_upload_v2(
                filename="stacktrace.txt",
                content=stacktrace_string,
                channel="C079AQN3HE2",
                title="Stacktrace",
                initial_comment="The stacktrace for the error above",
            )
        except SlackApiError as e:
            LOG.error(
                f"Failed upload stacktrace. Response from slack: {e.response["error"]}, {e}"
            )
            return

    @staticmethod
    def build_section(text: str, is_markdown=False):
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn" if is_markdown else "plain_text",
                "text": text,
            },
        }
