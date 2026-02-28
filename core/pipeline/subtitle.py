import logging
from pathlib import Path

from core.pipeline.base import PipelineContext
from core.utils import ensure_dir, escape_subtitle_filter_path, run_command, write_srt

logger = logging.getLogger(__name__)


class SubtitleStep:
    def execute(self, context: PipelineContext) -> PipelineContext:
        base_dir = Path(context.get("output_dir", "outputs"))
        srt_dir = ensure_dir(base_dir / "srt")
        output_dir = ensure_dir(base_dir / "subtitled")

        transcript = context.get("transcript", [])
        subtitled: list[dict] = []

        for clip in context.get("clip_files", []):
            start, end = clip["start"], clip["end"]
            local_entries = []
            for line in transcript:
                overlap_start = max(start, line["start"])
                overlap_end = min(end, line["end"])
                if overlap_end > overlap_start:
                    local_entries.append(
                        {
                            "start": overlap_start - start,
                            "end": overlap_end - start,
                            "text": line["text"],
                        }
                    )

            if not local_entries:
                local_entries = [{"start": 0.0, "end": max(end - start, 0.5), "text": clip.get("text", "Clip")[:120]}]

            clip_stem = Path(clip["path"]).stem
            srt_path = srt_dir / f"{clip_stem}.srt"
            write_srt(local_entries, srt_path)

            output_path = output_dir / f"{clip_stem}.mp4"
            subtitle_filter = f"subtitles='{escape_subtitle_filter_path(srt_path)}'"
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                clip["path"],
                "-vf",
                subtitle_filter,
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
            subtitled.append({**clip, "path": str(output_path), "subtitle": str(srt_path)})

        context["clip_files"] = subtitled
        return context
