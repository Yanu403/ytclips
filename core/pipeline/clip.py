import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from core.utils import ensure_dir, run_command

logger = logging.getLogger(__name__)


class ClipStep:
    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max_workers

    def execute(self, context: dict) -> dict:
        source_video = Path(context["source_video"])
        clip_defs = context.get("clips", [])
        clip_dir = ensure_dir(Path(context.get("output_dir", "outputs")) / "clips")

        def build_clip(index: int, clip_def: dict) -> dict:
            output_path = clip_dir / f"clip_{index:02}.mp4"
            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                f"{clip_def['start']:.3f}",
                "-to",
                f"{clip_def['end']:.3f}",
                "-i",
                str(source_video),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
            run_command(cmd)
            return {**clip_def, "path": str(output_path), "index": index}

        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(build_clip, idx, clip_def): idx
                for idx, clip_def in enumerate(clip_defs, start=1)
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results.append(future.result())
                except Exception:
                    logger.exception("Failed to produce clip %s", idx)

        context["clip_files"] = sorted(results, key=lambda item: item["index"])
        if not context["clip_files"]:
            raise RuntimeError("No clips were generated")
        return context
