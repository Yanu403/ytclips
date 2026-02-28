from __future__ import annotations

from typing import Any, Protocol

PipelineContext = dict[str, Any]


class PipelineStep(Protocol):
    def execute(self, context: PipelineContext) -> PipelineContext:
        ...
