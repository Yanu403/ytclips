import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


class GeminiAnalyzer:
    """Analyze transcript text with Gemini to extract high-engagement clip segments.

    The class performs a single API call that asks Gemini for both ranked segment
    windows and candidate titles. It validates and normalizes the JSON response,
    retries transient failures, and safely falls back to an empty result on
    malformed responses.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-1.5-flash",
        timeout_seconds: int = 30,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.5,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds

    def analyze(self, transcript_text: str) -> list[dict[str, Any]]:
        if not transcript_text or not transcript_text.strip():
            logger.warning("GeminiAnalyzer received empty transcript text")
            return []

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set; skipping Gemini analysis")
            return []

        prompt = self._build_prompt(transcript_text)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "response_mime_type": "application/json",
            },
        }

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )

        for attempt in range(1, self.max_retries + 1):
            try:
                raw = self._request(url, payload)
                parsed = self._extract_json_text(raw)
                validated = self._validate_response(parsed)
                if validated:
                    return validated
                logger.warning("GeminiAnalyzer returned no valid segments on attempt %d", attempt)
            except Exception as exc:
                logger.warning("GeminiAnalyzer attempt %d failed: %s", attempt, exc)

            if attempt < self.max_retries:
                sleep_s = self.retry_backoff_seconds * (2 ** (attempt - 1))
                time.sleep(sleep_s)

        logger.error("GeminiAnalyzer exhausted retries and returned no valid output")
        return []

    def _request(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        import requests

        response = requests.post(url, json=payload, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _build_prompt(transcript_text: str) -> str:
        clipped_text = transcript_text[:35000]
        return (
            "You are an expert viral short-form content editor. "
            "From the transcript below, extract the top 8 highest-engagement highlight segments.\n"
            "Constraints:\n"
            "- Exactly 8 segments if possible\n"
            "- Each segment duration must be between 20 and 45 seconds\n"
            "- Segments must NOT overlap\n"
            "- Prioritize emotional spikes, controversial opinions, and humor\n"
            "- score should be a float from 0 to 1\n"
            "- hook should be a compelling one-line hook\n"
            "- titles should include 3 short viral title options for the segment\n\n"
            "Return strictly valid JSON and nothing else in this format:\n"
            "[\n"
            "  {\n"
            "    \"start\": 12.3,\n"
            "    \"end\": 42.5,\n"
            "    \"score\": 0.93,\n"
            "    \"hook\": \"...\",\n"
            "    \"titles\": [\"...\", \"...\", \"...\"]\n"
            "  }\n"
            "]\n\n"
            "Transcript:\n"
            f"{clipped_text}"
        )

    @staticmethod
    def _extract_json_text(response_json: dict[str, Any]) -> Any:
        candidates = response_json.get("candidates") or []
        if not candidates:
            raise ValueError("Gemini response has no candidates")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise ValueError("Gemini response has no content parts")

        text = parts[0].get("text", "").strip()
        if not text:
            raise ValueError("Gemini response part is empty")

        return GeminiAnalyzer._safe_json_loads(text)

    @staticmethod
    def _safe_json_loads(text: str) -> Any:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            normalized = text.strip()
            if normalized.startswith("```"):
                normalized = normalized.strip("`")
                if normalized.startswith("json"):
                    normalized = normalized[4:].strip()
            return json.loads(normalized)

    @staticmethod
    def _validate_response(data: Any) -> list[dict[str, Any]]:
        if not isinstance(data, list):
            raise ValueError("Gemini response is not a JSON array")

        normalized: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue

            try:
                start = float(item["start"])
                end = float(item["end"])
                score = float(item["score"])
                hook = str(item["hook"]).strip()
                titles_raw = item["titles"]
            except (KeyError, TypeError, ValueError):
                continue

            if end <= start:
                continue

            duration = end - start
            if duration < 20 or duration > 45:
                continue

            if score < 0:
                score = 0.0
            if score > 1:
                score = 1.0

            if not isinstance(titles_raw, list):
                continue

            titles = [str(t).strip() for t in titles_raw if str(t).strip()]
            if not hook or not titles:
                continue

            normalized.append(
                {
                    "start": round(start, 3),
                    "end": round(end, 3),
                    "score": round(score, 4),
                    "hook": hook,
                    "titles": titles[:5],
                }
            )

        normalized.sort(key=lambda x: x["start"])
        non_overlapping: list[dict[str, Any]] = []
        for segment in normalized:
            if not non_overlapping or segment["start"] >= non_overlapping[-1]["end"]:
                non_overlapping.append(segment)

        non_overlapping.sort(key=lambda x: x["score"], reverse=True)
        return non_overlapping[:8]
