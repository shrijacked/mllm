from __future__ import annotations

import json
import logging
import re

import requests

from src.config import OPENAI_API_BASE

log = logging.getLogger(__name__)


class OpenAIJSONError(Exception):
    def __init__(self, message, raw_body=None):
        super().__init__(message)
        self.raw_body = raw_body


def _strip_json_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


class OpenAIClient:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model_preference = model
        self.model = model
        self._session = requests.Session()
        self._session.headers.update(
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )

    def _completion(self, messages, temperature, json_mode):
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        return self._session.post(
            f"{OPENAI_API_BASE}/chat/completions",
            json=body,
            timeout=120,
        )

    def _try_models(self, messages, temperature, json_mode):
        order = []
        for m in (self.model_preference, "gpt-4o-mini", "gpt-4o"):
            if m and m not in order:
                order.append(m)

        last_text = ""

        for m in order:
            self.model = m
            r = self._completion(messages, temperature, json_mode)
            if r.status_code == 200:
                log.info("openai model in use: %s", m)
                return r.json()

            last_text = r.text or ""
            if json_mode:
                r2 = self._completion(messages, temperature, False)
                if r2.status_code == 200:
                    log.info("openai model in use (no json_mode): %s", m)
                    return r2.json()
                last_text = r2.text or ""

        raise RuntimeError(f"OpenAI API error after model tries: {last_text[:500]}")

    def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        data = self._try_models(messages, temperature, json_mode)
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"unexpected OpenAI response shape: {data!r}") from e

    def chat_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        schema_hint: str | None = None,
    ) -> dict:
        u = user
        if schema_hint:
            u = f"{user}\n\nExpected JSON shape:\n{schema_hint}"

        def parse_once(text: str) -> dict:
            cleaned = _strip_json_fences(text)
            return json.loads(cleaned)

        text = self.chat(system, u, temperature=temperature, json_mode=True)
        try:
            return parse_once(text)
        except json.JSONDecodeError:
            reminder = (
                "Your previous response was not valid JSON. Return only a single JSON object "
                "- no markdown fences, no prose."
            )
            text2 = self.chat(
                system,
                u + "\n\n" + reminder,
                temperature=temperature,
                json_mode=True,
            )
            try:
                return parse_once(text2)
            except json.JSONDecodeError as e:
                raise OpenAIJSONError(str(e), raw_body=text2) from e
