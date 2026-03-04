from __future__ import annotations

from typing import Any, Protocol, TypedDict


class PipelineContext(TypedDict, total=False):
    url: str
    output_dir: str
    duration: float
    video_id: str
    video_title: str
    video_description: str
    source_video: str
    transcript: list[dict[str, Any]]
    clips: list[dict[str, Any]]
    clip_files: list[dict[str, Any]]


class PipelineStep(Protocol):
    def execute(self, context: PipelineContext) -> PipelineContext:
        ...
