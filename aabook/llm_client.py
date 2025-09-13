import json
import os
import re
from typing import Any, Dict, Optional

from openai import OpenAI

# Auto-load environment variables from a local .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # If python-dotenv is not installed, ignore; env vars can still come from the shell
    pass


class LLMClient:
    """Thin wrapper around OpenAI chat completions optimized for JSON outputs."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.model = model
        effective_api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not effective_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Provide via .env, env var, or LLMClient(api_key=...)."
            )

        client_kwargs: Dict[str, Any] = {"api_key": effective_api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self._client = OpenAI(**client_kwargs)

    def _extract_json(self, content: str) -> Dict[str, Any]:
        """Attempt to parse JSON from a model response, robust to extra text or fences."""
        # Try direct parse first
        try:
            return json.loads(content)
        except Exception:
            pass

        # Remove code fences if present
        fenced_match = re.search(r"```(?:json)?\n([\s\S]*?)\n```", content)
        if fenced_match:
            fenced = fenced_match.group(1)
            try:
                return json.loads(fenced)
            except Exception:
                content = fenced  # fall through to brace slicing

        # Slice from first '{' to last '}'
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(content[start : end + 1])
            except Exception:
                pass
        raise ValueError("Model response did not contain valid JSON.")

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        completion = self._client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = completion.choices[0].message.content or "{}"
        return self._extract_json(content)
