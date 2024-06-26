import traceback

import requests

from tapir import settings


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
            "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",  # TODO use Token from ENV, don't commit it!
        }
        requests.post(url, json=data, headers=headers)
