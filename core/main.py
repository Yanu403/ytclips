import argparse
import json
import logging
from pathlib import Path
from urllib.parse import urlparse

from core.pipeline import (
    AnalyzeStep,
    ClipStep,
    DownloadStep,
    SmartCropStep,
    SubtitleStep,
    ThumbnailStep,
    TitleGeneratorStep,
    TranscriptStep,
)
from core.pipeline.base import PipelineContext, PipelineStep
from core.utils import configure_logging, ensure_dir, require_binary

logger = logging.getLogger(__name__)

_ALLOWED_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
}


class PipelineError(RuntimeError):
    def __init__(self, step: str, cause: Exception) -> None:
        self.step = step
        self.cause = cause
        super().__init__(f"Step {step} failed: {cause}")


class PipelineRunner:
    def __init__(self, steps: list[PipelineStep], verbose: bool = False) -> None:
        self.steps = steps
        self.verbose = verbose

    def run(self, context: PipelineContext) -> PipelineContext:
        for step in self.steps:
            step_name = step.__class__.__name__
            logger.info("Starting step: %s", step_name)
            try:
                context = step.execute(context)
            except Exception as exc:
                if self.verbose:
                    logger.exception("Pipeline failed at %s", step_name)
                else:
                    logger.error("Pipeline failed at %s: %s", step_name, exc)
                raise PipelineError(step_name, exc) from exc
            logger.info("Finished step: %s", step_name)
        return context


def build_steps(args: argparse.Namespace) -> list[PipelineStep]:
    return [
        DownloadStep(),
        TranscriptStep(),
        AnalyzeStep(target_clip_length=args.clip_length, max_clips=args.max_clips),
        ClipStep(max_workers=args.workers),
        SmartCropStep(),
        SubtitleStep(),
        ThumbnailStep(),
        TitleGeneratorStep(),
    ]


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("--url must use https scheme")
    if parsed.netloc.lower() not in _ALLOWED_YOUTUBE_HOSTS:
        raise ValueError("--url must be a YouTube URL (youtube.com or youtu.be)")
    return url


def _validated_output_dir(path_value: str, base_dir: Path, allow_outside: bool) -> Path:
    output_path = Path(path_value).expanduser()
    if not output_path.is_absolute():
        output_path = (base_dir / output_path).resolve()
    else:
        output_path = output_path.resolve()

    if not allow_outside:
        try:
            output_path.relative_to(base_dir)
        except ValueError as exc:
            raise ValueError(
                f"--output-dir must be inside {base_dir} unless --allow-outside-output-dir is set"
            ) from exc
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YouTube auto-clip pipeline")
    parser.add_argument("--url", required=True, help="YouTube URL to process")
    parser.add_argument("--output-dir", default="outputs", help="Output directory")
    parser.add_argument("--allow-outside-output-dir", action="store_true", help="Allow writing output outside cwd")
    parser.add_argument("--clip-length", type=float, default=30.0, help="Target clip length in seconds")
    parser.add_argument("--max-clips", type=int, default=5, help="Maximum number of clips")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers for clip rendering")
    parser.add_argument("--verbose", action="store_true", help="Enable traceback logging")
    args = parser.parse_args()

    if args.clip_length <= 0:
        parser.error("--clip-length must be > 0")
    if args.max_clips <= 0:
        parser.error("--max-clips must be > 0")
    if args.workers <= 0:
        parser.error("--workers must be > 0")

    try:
        args.url = _validate_url(args.url)
        args.output_dir = str(
            _validated_output_dir(args.output_dir, base_dir=Path.cwd().resolve(), allow_outside=args.allow_outside_output_dir)
        )
    except ValueError as exc:
        parser.error(str(exc))

    return args


def _normalize_clip_files(clip_files: object) -> list[dict[str, object]]:
    if not isinstance(clip_files, list):
        return []

    normalized: list[dict[str, object]] = []
    for item in clip_files:
        if not isinstance(item, dict):
            continue
        clean_item: dict[str, object] = {}
        for key, value in item.items():
            if isinstance(value, Path):
                clean_item[key] = str(value)
            else:
                clean_item[key] = value
        normalized.append(clean_item)
    return normalized


def _write_manifest_atomic(manifest_path: Path, payload: object) -> None:
    temp_path = manifest_path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(manifest_path)


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

    runner = PipelineRunner(build_steps(args), verbose=args.verbose)
    try:
        result = runner.run(context)
    except PipelineError as exc:
        logger.error("Pipeline aborted at %s: %s", exc.step, exc.cause)
        raise SystemExit(1) from exc

    manifest_path = output_dir / "manifest.json"
    manifest_payload = _normalize_clip_files(result.get("clip_files", []))
    _write_manifest_atomic(manifest_path, manifest_payload)
    logger.info("Pipeline complete. Manifest: %s", manifest_path)


if __name__ == "__main__":
    main()
