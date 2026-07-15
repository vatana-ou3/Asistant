from __future__ import annotations

import os
from pathlib import Path

import psutil


PROJECT_ROOT = Path(__file__).resolve().parent
APP_PATH = os.path.normcase(str(PROJECT_ROOT / "app.py"))
READY_FILE = PROJECT_ROOT / "runtime" / "ahmark.ready"


def is_ahmark_wake_process(command_line: list[str]) -> bool:
    if "--wake-word" not in command_line:
        return False

    for argument in command_line:
        if not argument.lower().endswith("app.py"):
            continue
        resolved = os.path.normcase(os.path.abspath(argument))
        if resolved == APP_PATH:
            return True
    return False


def main() -> int:
    processes = []
    for process in psutil.process_iter(["pid", "cmdline"]):
        try:
            command_line = process.info["cmdline"] or []
            if process.pid != os.getpid() and is_ahmark_wake_process(command_line):
                processes.append(process)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

    for process in processes:
        try:
            process.terminate()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass

    _, alive = psutil.wait_procs(processes, timeout=3)
    for process in alive:
        try:
            process.kill()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass

    READY_FILE.unlink(missing_ok=True)
    if processes:
        print("Ah Mark has stopped.")
    else:
        print("Ah Mark is not running.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
