from pathlib import Path
from typing import Iterable


def format_srt_timestamp(seconds: float) -> str:
    millis = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1_000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def write_srt(entries: Iterable[dict], output_path: Path) -> None:
    lines: list[str] = []
    for index, entry in enumerate(entries, start=1):
        start = format_srt_timestamp(entry["start"])
        end = format_srt_timestamp(entry["end"])
        text = str(entry["text"]).strip() or "..."
        lines.extend([str(index), f"{start} --> {end}", text, ""])
    output_path.write_text("\n".join(lines), encoding="utf-8")
