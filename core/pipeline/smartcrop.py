import logging
from pathlib import Path

from core.utils import ensure_dir, run_command

logger = logging.getLogger(__name__)


class SmartCropStep:
    def execute(self, context: dict) -> dict:
        output_dir = ensure_dir(Path(context.get("output_dir", "outputs")) / "smartcrop")
        processed: list[dict] = []

        for clip in context.get("clip_files", []):
            input_path = Path(clip["path"])
            output_path = output_dir / input_path.name
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-vf",
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                str(output_path),
            ]
            run_command(cmd)
            processed.append({**clip, "path": str(output_path)})

        if not processed:
            raise RuntimeError("SmartCropStep received no clips")
        logger.info("Smart crop complete for %d clips", len(processed))
        context["clip_files"] = processed
        return context
