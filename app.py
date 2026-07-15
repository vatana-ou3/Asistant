from __future__ import annotations

import argparse
import sys

from actions.executor import ActionExecutor
from assistant.command_validator import CommandValidator
from assistant.conversation import OllamaConversation
from assistant.intent_detector import IntentDetector
from assistant.response_generator import ResponseGenerator
from audio.recorder import AudioRecorder
from audio.speaker import Speaker
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
        default=10.0,
        metavar="SECONDS",
        help="Maximum recording duration for each voice command (default: 10).",
    )
    parser.add_argument(
        "--whisper-model",
        default="tiny.en",
        metavar="MODEL",
        help="Faster-Whisper model to use (default: tiny.en; use base.en for better English accuracy).",
    )
    parser.add_argument(
        "--no-speech",
        action="store_true",
        help="Disable spoken responses in voice mode.",
    )
    return parser


def create_conversation() -> OllamaConversation:
    config = load_config()
    return OllamaConversation(
        model=config.settings.ollama_model,
        base_url=config.settings.ollama_url,
        assistant_name=config.settings.assistant_name,
    )


def create_speaker(disabled: bool = False) -> Speaker | None:
    config = load_config()
    if disabled or not config.settings.speech_enabled:
        return None
    return Speaker(rate=config.settings.speech_rate)


def speak_response(speaker: Speaker | None, response: str) -> None:
    if speaker is None:
        return
    try:
        speaker.speak(response)
    except Exception as exc:
        print(f"Speech output failed: {exc}")


def handle_command(
    command_text: str,
    dry_run: bool = False,
    conversation: OllamaConversation | None = None,
) -> str:
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
        if intent.action == "unknown" and conversation is not None:
            try:
                response = conversation.reply(command_text)
            except RuntimeError as exc:
                logger.error("Conversation failed: %s", exc)
                return f"Conversation failed: {exc}"
            logger.info("Conversation prompt=%r status=successful", command_text)
            return response

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
    conversation = create_conversation()
    assistant_name = load_config().settings.assistant_name
    print(f"{assistant_name} desktop assistant MVP")
    try:
        conversation.prepare()
    except RuntimeError as exc:
        print(f"Conversation unavailable: {exc}")
        conversation = None
    print("Type a command or message, or 'quit' to exit.")
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
        print(handle_command(command_text, dry_run=dry_run, conversation=conversation))


def process_voice_command(
    recorder: AudioRecorder,
    speech_detector: SpeechDetector,
    transcriber: Transcriber,
    record_seconds: float,
    dry_run: bool = False,
    conversation: OllamaConversation | None = None,
) -> str:
    if record_seconds <= 0:
        return "Recording duration must be greater than zero."

    try:
        print(f"Listening (stops when you finish, max {record_seconds:g} seconds)...")
        recording = recorder.record_command(record_seconds)
        input_level = speech_detector.input_level(recording)
        if not speech_detector.contains_speech(recording):
            return f"I did not hear any speech (microphone level: {input_level:.6f})."
        command_text = transcriber.transcribe(recording)
    except RuntimeError as exc:
        return str(exc)
    except Exception as exc:
        return f"Voice input failed: {exc}"

    if not command_text:
        return "I could not understand the recording."

    print(f"Heard: {command_text}")
    return handle_command(command_text, dry_run=dry_run, conversation=conversation)


def listen_once(
    record_seconds: float,
    whisper_model: str,
    dry_run: bool = False,
    speech_disabled: bool = False,
) -> str:
    transcriber = Transcriber(model_size=whisper_model)
    speaker = create_speaker(disabled=speech_disabled)
    conversation = create_conversation()
    try:
        print("Loading speech model...")
        transcriber.prepare()
    except Exception as exc:
        return f"Could not load speech model: {exc}"
    if speaker is not None:
        try:
            speaker.prepare()
        except Exception as exc:
            print(f"Speech output disabled: {exc}")
            speaker = None
    try:
        conversation.prepare()
    except RuntimeError as exc:
        print(f"Conversation unavailable: {exc}")
        conversation = None

    response = process_voice_command(
        AudioRecorder(),
        SpeechDetector(),
        transcriber,
        record_seconds,
        dry_run=dry_run,
        conversation=conversation,
    )
    speak_response(speaker, response)
    return response


def voice_loop(
    record_seconds: float,
    whisper_model: str,
    dry_run: bool = False,
    speech_disabled: bool = False,
) -> int:
    recorder = AudioRecorder()
    speech_detector = SpeechDetector()
    transcriber = Transcriber(model_size=whisper_model)
    conversation = create_conversation()
    speaker = create_speaker(disabled=speech_disabled)
    assistant_name = load_config().settings.assistant_name

    print(f"{assistant_name} push-to-talk voice mode")
    print("Loading speech and conversation models...")
    try:
        transcriber.prepare()
    except Exception as exc:
        print(f"Could not load speech model: {exc}")
        return 1
    if speaker is not None:
        try:
            speaker.prepare()
        except Exception as exc:
            print(f"Speech output disabled: {exc}")
            speaker = None
    try:
        conversation.prepare()
    except RuntimeError as exc:
        print(f"Conversation unavailable: {exc}")
        conversation = None
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

        response = process_voice_command(
            recorder,
            speech_detector,
            transcriber,
            record_seconds,
            dry_run=dry_run,
            conversation=conversation,
        )
        print(response)
        speak_response(speaker, response)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command:
        print(handle_command(args.command, dry_run=args.dry_run, conversation=create_conversation()))
        return 0
    if args.voice_once:
        print(
            listen_once(
                args.record_seconds,
                args.whisper_model,
                dry_run=args.dry_run,
                speech_disabled=args.no_speech,
            )
        )
        return 0
    if args.voice:
        return voice_loop(
            args.record_seconds,
            args.whisper_model,
            dry_run=args.dry_run,
            speech_disabled=args.no_speech,
        )
    return interactive_loop(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
