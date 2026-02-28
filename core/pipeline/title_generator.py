import logging

from core.services import GeminiClient

logger = logging.getLogger(__name__)


class TitleGeneratorStep:
    def __init__(self, gemini_client: GeminiClient | None = None) -> None:
        self.gemini_client = gemini_client or GeminiClient()

    def execute(self, context: dict) -> dict:
        for clip in context.get("clip_files", []):
            clip_text = clip.get("text") or context.get("video_title", "")
            title = self.gemini_client.generate_title(clip_text)
            clip["title"] = title
            logger.info("Generated title for clip_%02d: %s", clip["index"], title)
        return context
