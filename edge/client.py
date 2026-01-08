from __future__ import annotations

import os
from typing import Any, Dict

import requests
from requests import Response

from edge.core.events import QuietEyeEvent


class QuietEyeBackendClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def from_env() -> "QuietEyeBackendClient":
        base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        return QuietEyeBackendClient(base_url)

    def post_event(self, event: QuietEyeEvent, timeout_s: int = 10) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/events"
        payload = event.model_dump(mode="json")

        resp: Response = requests.post(url, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        return resp.json()

