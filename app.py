from __future__ import annotations

import argparse
import sys

from actions.executor import ActionExecutor
from assistant.command_validator import CommandValidator
from assistant.intent_detector import IntentDetector
from assistant.response_generator import ResponseGenerator
from audio.recorder import AudioRecorder
from audio.speech_detector import SpeechDetector
from audio.transcriber import Transcriber
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
    voice_group = parser.add_mutually_exclusive_group()
    voice_group.add_argument(
        "--voice",
        action="store_true",
        help="Start push-to-talk voice mode. Press Enter before each command.",
    )
    voice_group.add_argument(
        "--voice-once",
        action="store_true",
        help="Record and run one voice command, then exit.",
    )
    parser.add_argument(
        "--record-seconds",
        type=float,
        default=5.0,
        metavar="SECONDS",
        help="Recording duration for each voice command (default: 5).",
    )
    parser.add_argument(
        "--whisper-model",
        default="tiny.en",
        metavar="MODEL",
        help="Faster-Whisper model to use (default: tiny.en; use base.en for better English accuracy).",
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


def process_voice_command(
    recorder: AudioRecorder,
    speech_detector: SpeechDetector,
    transcriber: Transcriber,
    record_seconds: float,
    dry_run: bool = False,
) -> str:
    if record_seconds <= 0:
        return "Recording duration must be greater than zero."

    try:
        print(f"Listening (stops when you finish, max {record_seconds:g} seconds)...")
        recording = recorder.record_command(record_seconds)
        input_level = speech_detector.input_level(recording)
        if input_level < speech_detector.minimum_rms:
            return f"I did not hear any speech (microphone level: {input_level:.6f})."
        command_text = transcriber.transcribe(recording)
    except RuntimeError as exc:
        return str(exc)
    except Exception as exc:
        return f"Voice input failed: {exc}"

    if not command_text:
        return "I could not understand the recording."

    print(f"Heard: {command_text}")
    return handle_command(command_text, dry_run=dry_run)


def listen_once(record_seconds: float, whisper_model: str, dry_run: bool = False) -> str:
    transcriber = Transcriber(model_size=whisper_model)
    try:
        print("Loading speech model...")
        transcriber.prepare()
    except Exception as exc:
        return f"Could not load speech model: {exc}"

    return process_voice_command(
        AudioRecorder(),
        SpeechDetector(),
        transcriber,
        record_seconds,
        dry_run=dry_run,
    )


def voice_loop(record_seconds: float, whisper_model: str, dry_run: bool = False) -> int:
    recorder = AudioRecorder()
    speech_detector = SpeechDetector()
    transcriber = Transcriber(model_size=whisper_model)

    print("Nova push-to-talk voice mode")
    print("Loading speech model...")
    try:
        transcriber.prepare()
    except Exception as exc:
        print(f"Could not load speech model: {exc}")
        return 1
    print("Press Enter to record, or type 'quit' to exit.")
    while True:
        try:
            choice = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if choice in {"quit", "exit"}:
            return 0
        if choice:
            print("Press Enter to record, or type 'quit' to exit.")
            continue

        print(
            process_voice_command(
                recorder,
                speech_detector,
                transcriber,
                record_seconds,
                dry_run=dry_run,
            )
        )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command:
        print(handle_command(args.command, dry_run=args.dry_run))
        return 0
    if args.voice_once:
        print(listen_once(args.record_seconds, args.whisper_model, dry_run=args.dry_run))
        return 0
    if args.voice:
        return voice_loop(args.record_seconds, args.whisper_model, dry_run=args.dry_run)
    return interactive_loop(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
