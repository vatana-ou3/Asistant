# Offline Voice-Controlled Desktop Assistant

Nova is a Windows-focused desktop assistant prototype. This first version accepts typed commands, detects intents with rules, validates them for safety, and executes common desktop actions through optional local automation libraries.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python app.py --dry-run
```

Try commands such as:

```text
open chrome
open youtube
search google for FastAPI tutorials
search youtube for Python tutorials
copy
paste
scroll down
next tab
set volume to 50 percent
increase brightness
lock computer
```

Use `--dry-run` to test command parsing and validation without controlling the desktop:

```powershell
.\.venv\Scripts\python app.py --command "set volume to 80 percent" --dry-run
```

Use push-to-talk voice mode:

```powershell
.\.venv\Scripts\python app.py --voice
```

Press Enter, speak during the recording window, and wait for Nova to run the command. To record only one command, use `--voice-once`. The default recording window is five seconds; change it with `--record-seconds 8`.

Faster-Whisper downloads the selected model the first time it is used. Once the model is cached, transcription runs locally without an internet connection.

## Current Scope

- Rule-based command understanding.
- Application and website launching.
- Browser search URL creation.
- Keyboard shortcuts, scrolling, click commands.
- Volume and brightness actions, with media-key volume fallback when exact control is unavailable.
- Push-to-talk voice commands using local Faster-Whisper transcription.
- Safety validation for dangerous or invalid actions.
- Logging to `logs/assistant.log`.

Wake word detection and local LLM intent detection are planned for later phases.
