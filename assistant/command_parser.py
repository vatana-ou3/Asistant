from __future__ import annotations

import re


FILLER_PREFIXES = (
    "please ",
    "can you ",
    "could you ",
    "would you ",
    "nova ",
    "hey nova ",
)


def normalize_command(text: str) -> str:
    command = text.strip().lower()
    command = re.sub(r"[^\w\s%-]", " ", command)
    command = re.sub(r"\s+", " ", command).strip()

    changed = True
    while changed:
        changed = False
        for prefix in FILLER_PREFIXES:
            if command.startswith(prefix):
                command = command[len(prefix) :].strip()
                changed = True

    return command
