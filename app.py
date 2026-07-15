from __future__ import annotations

import argparse
import sys
import threading
import time
from pathlib import Path

from actions.executor import ActionExecutor
from assistant.command_validator import CommandValidator
from assistant.command_parser import normalize_command
from assistant.conversation import OllamaConversation
from assistant.intent_detector import IntentDetector
from assistant.response_generator import ResponseGenerator
from audio.recorder import AudioRecorder
from audio.speaker import Speaker
from audio.speech_detector import SpeechDetector
from audio.transcriber import Transcriber
from audio.wake_word import WakeWordDetector
from config.config import load_config
from interface.cli import AssistantCLI
from interface.tray import TrayController
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
    voice_group.add_argument(
        "--wake-word",
        action="store_true",
        help="Wait for the configured wake phrase, then enter hands-free follow-up mode.",
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
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Use plain text output instead of the styled CLI.",
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

    command_config = {**config.commands, "applications": config.applications}
    detector = IntentDetector(command_config)
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


def is_desktop_command(command_text: str) -> bool:
    return detect_command_action(command_text) is not None


def detect_command_action(command_text: str) -> str | None:
    config = load_config()
    command_config = {**config.commands, "applications": config.applications}
    intent = IntentDetector(command_config).detect(command_text)
    if CommandValidator().validate(intent).is_valid:
        return intent.action
    return None


def interactive_loop(dry_run: bool = False, plain: bool = False) -> int:
    conversation = create_conversation()
    config = load_config()

    if plain:
        print(f"{config.settings.assistant_name} desktop assistant")
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

    cli = AssistantCLI(config.settings.assistant_name, config.settings.ollama_model)
    cli.show_header()
    try:
        with cli.loading_status("Loading local model..."):
            conversation.prepare()
    except RuntimeError as exc:
        cli.console.print(f"[yellow]Conversation unavailable:[/yellow] {exc}")
        conversation = None

    return cli.interactive(
        lambda command: handle_command(command, dry_run=dry_run, conversation=conversation),
        is_desktop_command,
    )


def process_voice_command(
    recorder: AudioRecorder,
    speech_detector: SpeechDetector,
    transcriber: Transcriber,
    record_seconds: float,
    dry_run: bool = False,
    conversation: OllamaConversation | None = None,
) -> str:
    command_text, error = capture_voice_command(recorder, speech_detector, transcriber, record_seconds)
    if error:
        return error
    return handle_command(command_text, dry_run=dry_run, conversation=conversation)


def capture_voice_command(
    recorder: AudioRecorder,
    speech_detector: SpeechDetector,
    transcriber: Transcriber,
    record_seconds: float,
    listening_enabled: threading.Event | None = None,
) -> tuple[str | None, str | None]:
    if record_seconds <= 0:
        return None, "Recording duration must be greater than zero."

    try:
        print(f"Listening (stops when you finish, max {record_seconds:g} seconds)...")
        if listening_enabled is None:
            recording = recorder.record_command(record_seconds)
        else:
            recording = recorder.record_command(
                record_seconds,
                cancellation_event=listening_enabled,
            )
        input_level = speech_detector.input_level(recording)
        if not speech_detector.contains_speech(recording):
            return None, f"I did not hear any speech (microphone level: {input_level:.6f})."
        command_text = transcriber.transcribe(recording)
    except RuntimeError as exc:
        return None, str(exc)
    except Exception as exc:
        return None, f"Voice input failed: {exc}"

    if not command_text:
        return None, "I could not understand the recording."

    print(f"Heard: {command_text}")
    return command_text, None


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


def _play_cue(frequency: int) -> None:
    try:
        import winsound

        winsound.Beep(frequency, 120)
    except Exception:
        pass


def _acquire_wake_word_instance() -> bool:
    if sys.platform != "win32":
        return True

    import ctypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, "Local\\AhMarkVoiceAssistant")
    if kernel32.GetLastError() == 183:
        kernel32.CloseHandle(handle)
        return False
    global _WAKE_WORD_MUTEX
    _WAKE_WORD_MUTEX = handle
    return True


def _wake_ready_file() -> Path:
    return Path(__file__).resolve().parent / "runtime" / "ahmark.ready"


def wake_word_loop(
    record_seconds: float,
    whisper_model: str,
    dry_run: bool = False,
    speech_disabled: bool = False,
) -> int:
    if not _acquire_wake_word_instance():
        print("Ah Mark wake-word mode is already running.")
        return 0

    ready_file = _wake_ready_file()
    ready_file.unlink(missing_ok=True)
    config = load_config()
    recorder = AudioRecorder()
    speech_detector = SpeechDetector()
    transcriber = Transcriber(model_size=whisper_model)
    conversation = create_conversation()
    speaker = create_speaker(disabled=speech_disabled)
    wake_detector = WakeWordDetector(config.settings.wake_word_model, config.settings.wake_word)

    print(f"{config.settings.assistant_name} wake-word mode")
    print("Loading wake-word, speech, and conversation models...")
    try:
        wake_detector.prepare()
        transcriber.prepare()
    except Exception as exc:
        print(f"Could not start wake-word mode: {exc}")
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

    tray: TrayController | None = TrayController(config.settings.assistant_name)
    try:
        tray.start()
    except RuntimeError as exc:
        print(f"Tray controls unavailable: {exc}")
        tray = None

    ready_file.parent.mkdir(parents=True, exist_ok=True)
    ready_file.write_text(str(config.settings.assistant_name), encoding="utf-8")
    ready_message = f"I'm ready. Say {config.settings.wake_word} when you need me."
    print(ready_message)
    speak_response(speaker, ready_message)

    stop_phrases = {"bye", "goodbye", "stop listening", "go to sleep", "standby"}
    exit_phrases = {"exit ah mark", "quit ah mark", "shutdown ah mark"}
    try:
        while True:
            print(f"Standby: say '{config.settings.wake_word}'.")
            wake_detector.listen(tray.listening_enabled if tray is not None else None)
            _play_cue(880)
            print("Activated. Speak after the tone.")
            active_until = time.monotonic() + config.settings.follow_up_seconds
            scrolling_active = False

            while time.monotonic() < active_until:
                if tray is not None and not tray.listening_enabled.is_set():
                    if scrolling_active:
                        handle_command("stop scrolling", dry_run=dry_run)
                    break

                command_text, error = capture_voice_command(
                    recorder,
                    speech_detector,
                    transcriber,
                    record_seconds,
                    tray.listening_enabled if tray is not None else None,
                )
                if tray is not None and not tray.listening_enabled.is_set():
                    if scrolling_active:
                        handle_command("stop scrolling", dry_run=dry_run)
                    break
                if error:
                    if error.startswith("I did not hear any speech"):
                        continue
                    print(error)
                    break

                normalized_command = normalize_command(command_text)
                if normalized_command in exit_phrases:
                    if scrolling_active:
                        handle_command("stop scrolling", dry_run=dry_run)
                    response = "Shutting down. Goodbye."
                    print(response)
                    speak_response(speaker, response)
                    return 0

                if normalized_command in stop_phrases:
                    if scrolling_active:
                        handle_command("stop scrolling", dry_run=dry_run)
                    response = "Going back to standby."
                    print(response)
                    speak_response(speaker, response)
                    break

                command_action = detect_command_action(command_text)
                response = handle_command(command_text, dry_run=dry_run, conversation=conversation)
                print(response)
                speak_response(speaker, response)
                if command_action == "scroll":
                    scrolling_active = True
                    follow_up_prompt = "Scrolling slowly. Say stop when you want me to stop."
                elif command_action == "stop_scroll":
                    scrolling_active = False
                    follow_up_prompt = "Already done. What do you want next?"
                elif command_action is not None:
                    follow_up_prompt = "Already done. What do you want next?"
                else:
                    follow_up_prompt = "What do you want next?"
                print(follow_up_prompt)
                speak_response(speaker, follow_up_prompt)
                _play_cue(740)
                if scrolling_active:
                    active_until = float("inf")
                else:
                    active_until = time.monotonic() + config.settings.follow_up_seconds

            _play_cue(520)
    except KeyboardInterrupt:
        print()
        return 0
    finally:
        if tray is not None:
            tray.stop()
        ready_file.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command:
        conversation = create_conversation()
        if args.plain:
            print(handle_command(args.command, dry_run=args.dry_run, conversation=conversation))
            return 0

        config = load_config()
        cli = AssistantCLI(config.settings.assistant_name, config.settings.ollama_model)
        cli.show_header()
        cli.run_command(
            args.command,
            lambda command: handle_command(command, dry_run=args.dry_run, conversation=conversation),
            is_desktop_command,
        )
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
    if args.wake_word:
        return wake_word_loop(
            args.record_seconds,
            args.whisper_model,
            dry_run=args.dry_run,
            speech_disabled=args.no_speech,
        )
    return interactive_loop(dry_run=args.dry_run, plain=args.plain)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
