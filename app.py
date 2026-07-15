from __future__ import annotations

import argparse
import sys

from actions.executor import ActionExecutor
from assistant.command_validator import CommandValidator
from assistant.intent_detector import IntentDetector
from assistant.response_generator import ResponseGenerator
from config.config import load_config
from utils.logger import configure_logging, get_logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline voice-controlled desktop assistant MVP.")
    parser.add_argument(
        "--command",
        "-c",
        help="Run one text command directly, for example: 'open chrome' or 'set volume to 50 percent'.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect and validate commands without controlling the desktop.",
    )
    return parser


def handle_command(command_text: str, dry_run: bool = False) -> str:
    config = load_config()
    configure_logging(config.settings.log_file)
    logger = get_logger(__name__)

    detector = IntentDetector(config.commands)
    validator = CommandValidator()
    executor = ActionExecutor(config, dry_run=dry_run)
    responder = ResponseGenerator()

    intent = detector.detect(command_text)
    validation = validator.validate(intent)

    if not validation.is_valid:
        response = responder.error(validation.message)
        logger.warning("Rejected command=%r intent=%s reason=%s", command_text, intent, validation.message)
        return response

    result = executor.execute(intent)
    if result.success:
        logger.info("Command=%r intent=%s status=successful", command_text, intent)
        return responder.success(intent, result.message)

    logger.error("Command=%r intent=%s status=failed error=%s", command_text, intent, result.message)
    return responder.error(result.message)


def interactive_loop(dry_run: bool = False) -> int:
    print("Nova desktop assistant MVP")
    print("Type a command, or 'quit' to exit.")
    while True:
        try:
            command_text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if command_text.lower() in {"quit", "exit"}:
            return 0
        if not command_text:
            continue
        print(handle_command(command_text, dry_run=dry_run))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command:
        print(handle_command(args.command, dry_run=args.dry_run))
        return 0
    return interactive_loop(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
