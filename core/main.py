import argparse
import json
import logging
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pipeline import (  # noqa: E402
    AnalyzeStep,
    ClipStep,
    DownloadStep,
    SmartCropStep,
    SubtitleStep,
    ThumbnailStep,
    TitleGeneratorStep,
    TranscriptStep,
)
from core.pipeline.base import PipelineContext, PipelineStep  # noqa: E402
from core.utils import configure_logging, ensure_dir, require_binary  # noqa: E402

logger = logging.getLogger(__name__)


class PipelineRunner:
    def __init__(self, steps: list[PipelineStep]) -> None:
        self.steps = steps

    def run(self, context: PipelineContext) -> PipelineContext:
        for step in self.steps:
            step_name = step.__class__.__name__
            logger.info("Starting step: %s", step_name)
            try:
                context = step.execute(context)
            except Exception as exc:
                logger.exception("Pipeline failed at %s: %s", step_name, exc)
                raise
            logger.info("Finished step: %s", step_name)
        return context


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YouTube auto-clip pipeline")
    parser.add_argument("--url", required=True, help="YouTube URL to process")
    parser.add_argument("--output-dir", default="outputs", help="Output directory")
    parser.add_argument("--clip-length", type=float, default=30.0, help="Target clip length in seconds")
    parser.add_argument("--max-clips", type=int, default=5, help="Maximum number of clips")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers for clip rendering")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging()

    require_binary("ffmpeg")
    require_binary("ffprobe")

    output_dir = ensure_dir(Path(args.output_dir))
    context: PipelineContext = {
        "url": args.url,
        "output_dir": str(output_dir),
    }

    runner = PipelineRunner(
        [
            DownloadStep(),
            TranscriptStep(),
            AnalyzeStep(target_clip_length=args.clip_length, max_clips=args.max_clips),
            ClipStep(max_workers=max(1, args.workers)),
            SmartCropStep(),
            SubtitleStep(),
            ThumbnailStep(),
            TitleGeneratorStep(),
        ]
    )
    result = runner.run(context)

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(result.get("clip_files", []), indent=2), encoding="utf-8")
    logger.info("Pipeline complete. Manifest: %s", manifest_path)


if __name__ == "__main__":
    main()
