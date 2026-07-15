from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Intent:
    action: str
    target: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    requires_confirmation: bool = False


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    message: str = ""


@dataclass(frozen=True)
class ActionResult:
    success: bool
    message: str
