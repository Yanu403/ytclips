import logging
from pathlib import Path

from core.utils import ensure_dir, run_command

logger = logging.getLogger(__name__)


class ThumbnailStep:
    def execute(self, context: dict) -> dict:
        thumb_dir = ensure_dir(Path(context.get("output_dir", "outputs")) / "thumbnails")

        for clip in context.get("clip_files", []):
            clip_path = Path(clip["path"])
            midpoint = max(0.1, (clip["end"] - clip["start"]) / 2)
            thumbnail_path = thumb_dir / f"{clip_path.stem}.jpg"
            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                f"{midpoint:.3f}",
                "-i",
                str(clip_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(thumbnail_path),
            ]
            run_command(cmd)
            clip["thumbnail"] = str(thumbnail_path)

        logger.info("Generated thumbnails for %d clips", len(context.get("clip_files", [])))
        return context
