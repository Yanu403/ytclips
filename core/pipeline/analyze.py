import logging

logger = logging.getLogger(__name__)


class AnalyzeStep:
    def __init__(self, target_clip_length: float = 30.0, max_clips: int = 5) -> None:
        self.target_clip_length = target_clip_length
        self.max_clips = max_clips

    def execute(self, context: dict) -> dict:
        transcript = context.get("transcript", [])
        clips: list[dict] = []

        if transcript:
            current_start = transcript[0]["start"]
            current_end = current_start
            text_buffer: list[str] = []

            for line in transcript:
                line_end = line["end"]
                text_buffer.append(line["text"])
                current_end = line_end
                if current_end - current_start >= self.target_clip_length:
                    clips.append(
                        {
                            "start": current_start,
                            "end": current_end,
                            "text": " ".join(text_buffer),
                        }
                    )
                    current_start = current_end
                    text_buffer = []
                    if len(clips) >= self.max_clips:
                        break

            if text_buffer and len(clips) < self.max_clips:
                clips.append({"start": current_start, "end": current_end, "text": " ".join(text_buffer)})

        duration = float(context.get("duration", 0))
        if not clips and duration > 0:
            chunk = min(self.target_clip_length, duration)
            start = 0.0
            while start < duration and len(clips) < self.max_clips:
                end = min(duration, start + chunk)
                clips.append({"start": start, "end": end, "text": context.get("video_title", "Clip")})
                start = end

        logger.info("Selected %d clip segments", len(clips))
        context["clips"] = clips
        return context
