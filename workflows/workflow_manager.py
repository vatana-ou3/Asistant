from __future__ import annotations

from pathlib import Path


class WorkflowManager:
    def __init__(self, workflow_file: Path) -> None:
        self.workflow_file = workflow_file

    def list_workflows(self) -> list[str]:
        return []
