import logging
import traceback

import requests

from tapir import settings

LOG = logging.getLogger(__name__)


class SendExceptionsToSlackMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as e:
            stacktrace_string = traceback.format_exc()
            self.send_slack_message(e, stacktrace_string)
            raise e
        return response

    def process_exception(self, _, exception):
        stacktrace_string = traceback.format_exc()
        self.send_slack_message(exception, stacktrace_string)
        return None

    @staticmethod
    def send_slack_message(e: Exception, stacktrace_string: str):
        if settings.DEBUG:
            return
        url = "https://slack.com/api/chat.postMessage"
        data = {
            "channel": "C079AQN3HE2",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Hi @channel! The following error happened on the production server :ladybug:",
                    },
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{e}",
                    },
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": stacktrace_string,
                    },
                },
            ],
        }
        headers = {
            "Content-type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",
        }
        response = requests.post(url, json=data, headers=headers)
        if not response.json().get("ok", False):
            LOG.error(
                f"Failed to send slack message. Response from slack: {response.text}"
            )
