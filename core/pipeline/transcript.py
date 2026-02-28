import logging
from pathlib import Path

from core.pipeline.base import PipelineContext
from core.utils import probe_duration

logger = logging.getLogger(__name__)


class TranscriptStep:
    def execute(self, context: PipelineContext) -> PipelineContext:
        source_video = Path(context["source_video"])
        duration = probe_duration(source_video)
        transcript = self._try_fetch_subtitles(context.get("url", ""))

        if not transcript:
            logger.warning("No subtitles found; creating fallback transcript from metadata")
            description = context.get("video_description") or context.get("video_title") or "Video clip"
            transcript = [{"start": 0.0, "end": duration, "text": str(description)[:500]}]

        context["duration"] = duration
        context["transcript"] = transcript
        return context

    def _try_fetch_subtitles(self, url: str) -> list[dict]:
        from yt_dlp import YoutubeDL

        if not url:
            return []

        ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitlesformat": "vtt",
            "quiet": True,
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as exc:
            logger.warning("Subtitle metadata lookup failed: %s", exc)
            return []

        subtitles = info.get("automatic_captions") or info.get("subtitles") or {}
        selected = self._select_track(subtitles)
        if selected is None or not selected.get("url"):
            return []

        try:
            import requests

            response = requests.get(selected["url"], timeout=15)
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Subtitle download failed: %s", exc)
            return []

        return self._parse_vtt(response.text)

    @staticmethod
    def _select_track(subtitles: dict) -> dict | None:
        preferred_langs = ("en", "en-US", "en-GB")
        for lang in preferred_langs:
            tracks = subtitles.get(lang) or []
            if tracks:
                vtt = [track for track in tracks if track.get("ext") == "vtt"]
                return vtt[0] if vtt else tracks[0]

        for tracks in subtitles.values():
            if tracks:
                vtt = [track for track in tracks if track.get("ext") == "vtt"]
                return vtt[0] if vtt else tracks[0]
        return None

    @staticmethod
    def _parse_vtt(vtt_text: str) -> list[dict]:
        entries: list[dict] = []
        lines = [line.strip("\ufeff") for line in vtt_text.splitlines()]

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if "-->" not in line:
                i += 1
                continue

            start_raw, end_raw = [part.strip() for part in line.split("-->", maxsplit=1)]
            i += 1
            text_parts: list[str] = []
            while i < len(lines) and lines[i].strip():
                text_parts.append(lines[i].strip())
                i += 1

            text = " ".join(text_parts)
            text = " ".join(text.replace("<c>", "").replace("</c>", "").split())
            if text:
                start_ts = TranscriptStep._parse_timestamp(start_raw)
                end_ts = TranscriptStep._parse_timestamp(end_raw.split(" ")[0])
                if end_ts > start_ts:
                    entries.append({"start": start_ts, "end": end_ts, "text": text})
            i += 1

        deduped: list[dict] = []
        for entry in entries:
            if not deduped or deduped[-1]["text"] != entry["text"] or deduped[-1]["end"] < entry["start"]:
                deduped.append(entry)
            else:
                deduped[-1]["end"] = max(deduped[-1]["end"], entry["end"])
        return deduped

    @staticmethod
    def _parse_timestamp(value: str) -> float:
        value = value.replace(",", ".")
        parts = value.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = parts
        else:
            hours = "0"
            minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
