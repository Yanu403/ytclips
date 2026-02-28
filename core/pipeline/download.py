import logging
from pathlib import Path

from core.pipeline.base import PipelineContext
from core.utils import ensure_dir

logger = logging.getLogger(__name__)


class DownloadStep:
    def execute(self, context: PipelineContext) -> PipelineContext:
        from yt_dlp import YoutubeDL

        url = context["url"]
        output_dir = ensure_dir(Path(context.get("output_dir", "outputs")) / "downloads")
        output_template = output_dir / "%(id)s.%(ext)s"

        ydl_opts = {
            "outtmpl": str(output_template),
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "quiet": True,
            "noprogress": True,
        }

        logger.info("Downloading source video from %s", url)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info["id"]
            requested_ext = "mp4"
            source_video = output_dir / f"{video_id}.{requested_ext}"
            if not source_video.exists():
                files = sorted(output_dir.glob(f"{video_id}.*"))
                if not files:
                    raise FileNotFoundError(f"Downloaded video not found for id={video_id}")
                source_video = files[-1]

        context.update(
            {
                "video_id": video_id,
                "video_title": info.get("title", ""),
                "source_video": str(source_video),
                "video_description": info.get("description", ""),
            }
        )
        return context
