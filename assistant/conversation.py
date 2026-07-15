from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaConversation:
    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:11434",
        assistant_name: str = "Ah Mark",
        history_limit: int = 12,
    ) -> None:
        self.model = model
        base_url = base_url.rstrip("/")
        self.endpoint = f"{base_url}/api/chat"
        self.generate_endpoint = f"{base_url}/api/generate"
        self.history_limit = history_limit
        self.messages = [
            {
                "role": "system",
                "content": (
                    f"You are {assistant_name}, a concise and friendly offline desktop assistant. "
                    "Answer conversational questions directly. Keep most replies under three sentences. "
                    "Do not claim that you performed a desktop action; desktop actions are handled separately."
                ),
            }
        ]

    def prepare(self) -> None:
        self._post(
            self.generate_endpoint,
            {
                "model": self.model,
                "prompt": "",
                "stream": False,
                "keep_alive": "10m",
            },
        )

    def reply(self, user_text: str) -> str:
        request_messages = [*self.messages, {"role": "user", "content": user_text}]
        payload = {
            "model": self.model,
            "messages": request_messages,
            "stream": False,
            "think": False,
            "keep_alive": "10m",
            "options": {"temperature": 0.4, "num_predict": 180},
        }
        result = self._post(self.endpoint, payload)

        content = result.get("message", {}).get("content", "").strip()
        if not content:
            raise RuntimeError("Ollama returned an empty response.")

        self.messages.extend(
            [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": content},
            ]
        )
        self.messages = [self.messages[0], *self.messages[1:][-self.history_limit :]]
        return content

    @staticmethod
    def _post(endpoint: str, payload: dict) -> dict:
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=120) as response:
                return json.load(response)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError("Could not reach Ollama. Make sure the Ollama app is running.") from exc
