import json

import requests
from django.conf import settings


class CoopsPtRequestHandler:
    @staticmethod
    def get(url: str):
        return requests.get(
            url=f"{settings.COOPS_PT_API_BASE_URL}/{url}",
            headers={
                "Accept": "application/json",
                "Api-Secret": settings.COOPS_PT_API_KEY,
            },
        )

    @staticmethod
    def post(url: str, data: dict):
        return requests.post(
            url=f"{settings.COOPS_PT_API_BASE_URL}/{url}",
            headers={"Accept": "application/json"},
            data=json.dumps(data),
        )
