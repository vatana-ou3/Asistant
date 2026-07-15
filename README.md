# Offline Voice-Controlled Desktop Assistant

Ah Mark is a Windows-focused desktop assistant prototype. This first version accepts typed commands, detects intents with rules, validates them for safety, and executes common desktop actions through optional local automation libraries.

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

Press Enter, speak during the recording window, and wait for Ah Mark to run the command. To record only one command, use `--voice-once`. Recording stops after you finish speaking, with a default maximum of ten seconds; change it with `--record-seconds 15`.

Voice-mode responses are spoken through Windows text-to-speech and remain visible in the terminal. Use `--no-speech` to keep responses silent.

Use hands-free wake-word mode:

```powershell
.\.venv\Scripts\python app.py --wake-word
```

Say "Hey bro" and wait for the activation tone before speaking. After completing a desktop task, Ah Mark says "Already done. What do you want next?" and plays a follow-up tone. Speak the next request immediately without repeating the wake phrase. Follow-up mode remains active for 30 seconds. Say "bye" to return to wake-word standby immediately. Say "exit Ah Mark" to stop the background assistant.

The `load-ahmark` command starts wake-word mode in a minimized window, waits for all local models to load, and reports when Ah Mark is ready. Ah Mark also announces readiness through text-to-speech.

Stop the background listener from any CMD window with `stop-ahmark`.

Typed commands work at the same time as the background voice listener:

```cmd
ahmark open chrome
ahmark search youtube for Python tutorials
ahmark what is Python
```

Say or type `screenshot`, `take a screenshot`, or `open snipping tool` to launch Windows Snipping Tool and select the capture area manually.

Say or type `full screen` or `maximize window` to maximize the active app. Use `small screen` or `restore window` to return it to a normal resizable window.

In wake-word mode, `scroll down` and `scroll up` start slow continuous scrolling. Follow-up listening remains active until you say `stop` or `stop scrolling`.

Run `ahmark` without additional text to open the interactive typed conversation.

The typed interface includes a styled local-assistant header, clear conversation turns, loading indicators, automatic terminal wrapping, and Markdown/code rendering. Use `python app.py --plain` when unstyled output is preferable for scripting.

Ah Mark sends conversational requests that are not recognized desktop commands to the local Ollama model configured in `config/settings.json`. Conversation history is retained for the current session, while desktop actions continue to use the rule-based validator.

Faster-Whisper downloads the selected model the first time it is used. Once the model is cached, transcription runs locally without an internet connection.

## Current Scope

- Rule-based command understanding.
- Application and website launching.
- Browser search URL creation.
- Keyboard shortcuts, scrolling, click commands.
- Volume and brightness actions, with media-key volume fallback when exact control is unavailable.
- Push-to-talk voice commands using local Faster-Whisper transcription.
- Local conversation through Ollama using `frob/qwen3.5-instruct:4b`.
- Spoken voice-mode responses using Windows text-to-speech.
- Offline Vosk wake-word detection with a 30-second follow-up conversation window.
- Safety validation for dangerous or invalid actions.
- Logging to `logs/assistant.log`.

Wake word detection and local LLM intent detection are planned for later phases.
