import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model

    def generate_title(self, transcript_excerpt: str) -> str:
        prompt = (
            "Create a concise, viral, safe YouTube Shorts title in under 70 characters. "
            f"Context: {transcript_excerpt[:1200]}"
        )
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set, using heuristic title generation")
            return self._fallback_title(transcript_excerpt)

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            import requests

            response = requests.post(url, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return text.replace("\n", " ")[:70]
        except Exception as exc:
            logger.exception("Gemini request failed: %s", exc)
            return self._fallback_title(transcript_excerpt)

    @staticmethod
    def _fallback_title(transcript_excerpt: str) -> str:
        words = [w.strip(".,!?\"'()[]") for w in transcript_excerpt.split() if w.strip()]
        candidate = " ".join(words[:10]).strip()
        return (candidate[:67] + "...") if len(candidate) > 70 else (candidate or "Must-Watch Clip")
