import logging
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

logger = logging.getLogger(__name__)


class FFmpegError(RuntimeError):
    pass


def require_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise FFmpegError(f"Required binary not found on PATH: {name}")


def run_command(cmd: Sequence[str]) -> None:
    pretty_cmd = " ".join(shlex.quote(part) for part in cmd)
    logger.debug("Running command: %s", pretty_cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("Command failed: %s", pretty_cmd)
        logger.error("stderr: %s", result.stderr.strip())
        raise FFmpegError(result.stderr.strip() or "ffmpeg/ffprobe command failed")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def probe_duration(video_path: Path) -> float:
    require_binary("ffprobe")
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise FFmpegError(result.stderr.strip() or "failed to probe duration")
    return float(result.stdout.strip())


def escape_subtitle_filter_path(path: Path) -> str:
    raw = str(path)
    return raw.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
