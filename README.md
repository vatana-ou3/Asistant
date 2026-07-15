# Ah Mark

Ah Mark is a Windows desktop assistant that supports offline wake-word control, local speech recognition, spoken responses, desktop automation, and conversation through a local Ollama model.

## Requirements

- Windows 10 or Windows 11
- Python 3.11 or newer
- A working microphone
- [Ollama for Windows](https://ollama.com/download/windows)
- Approximately 5 GB of free space for Python packages and local models

## Install

Clone the repository and open PowerShell in the project directory:

```powershell
git clone <repository-url>
cd voice_assistant
```

Create an isolated Python environment and install all Python dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Install the configured conversation model:

```powershell
ollama pull frob/qwen3.5-instruct:4b
```

Another installed Ollama model can be selected through `ollama_model` in `config/settings.json`.

Download and extract the offline Vosk English model:

```powershell
New-Item -ItemType Directory -Path models -Force
Invoke-WebRequest `
  -Uri "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" `
  -OutFile "$env:TEMP\vosk-model-small-en-us-0.15.zip"
Expand-Archive `
  -LiteralPath "$env:TEMP\vosk-model-small-en-us-0.15.zip" `
  -DestinationPath models `
  -Force
```

Faster-Whisper downloads and caches `tiny.en` during its first voice-mode launch. Subsequent transcription runs locally.

## First Run

From the project directory, start hands-free voice mode with:

```cmd
load-ahmark.cmd
```

Wait until Ah Mark says:

```text
I'm ready. Say hey bro when you need me.
```

Then say **"Hey bro"**, wait for the activation tone, and speak your request.

Stop the background listener with:

```cmd
stop-ahmark.cmd
```

## Global Commands

Add the cloned project directory to your user `PATH` to use the commands from any new CMD window:

```powershell
$project = (Resolve-Path .).Path
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (($userPath -split ";") -notcontains $project) {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$project", "User")
}
```

Open a new terminal after changing `PATH`. These commands will then be available globally:

```cmd
load-ahmark
ahmark
ahmark open chrome
ahmark what is Python?
stop-ahmark
```

## Voice Workflow

1. Say **"Hey bro"**.
2. Wait for the activation tone.
3. Speak for up to 10 seconds.
4. Ah Mark performs the action or answers through Qwen.
5. After a desktop action, it says **"Already done. What do you want next?"**
6. Speak another request after the follow-up tone without repeating the wake phrase.

Follow-up mode remains active for 30 seconds after each completed request.

- **"Bye"** returns to wake-word standby.
- **"Exit Ah Mark"** closes the background assistant.
- **"Stop"** ends continuous scrolling.

## Typed CLI

Start the styled interactive CLI:

```cmd
ahmark
```

Run a single command or question:

```cmd
ahmark team
ahmark search youtube for Python tutorials
ahmark explain Python decorators
```

The CLI includes formatted conversation turns, loading indicators, terminal wrapping, Markdown, and highlighted code blocks.

Plain output remains available for scripts:

```powershell
.\.venv\Scripts\python.exe app.py --command "open chrome" --plain
```

## Desktop Controls

Ah Mark currently supports:

- Opening Chrome, Edge, VS Code, Teams, Telegram, File Explorer, Spotify, Notepad, and Calculator
- Opening YouTube, Google, GitHub, and Gmail
- Searching Google and YouTube
- Friendly names such as `team`, `folder`, `VS Code`, `YouTube`, and `Telegram`
- Continuous `scroll down` and `scroll up` until `stop` is heard
- Copy, paste, cut, undo, redo, save, refresh, and browser-tab shortcuts
- Mouse clicks and screen scrolling
- Volume, mute, and screen-brightness control
- Maximizing the active window with `full screen` or `maximize window`
- Restoring the active window with `small screen` or `restore window`
- Opening Windows Snipping Tool with `screenshot`
- Locking Windows

Shutdown and restart requests remain blocked by the safety validator.

## Configuration

Edit `config/settings.json` to change:

- Assistant name
- Wake phrase
- Follow-up duration
- Ollama model and server URL
- Speech output and speaking rate
- Vosk model location

Application aliases are stored in `config/applications.json`. Website and keyboard-shortcut aliases are stored in `config/commands.json`.

## Development

Run commands without controlling the desktop:

```powershell
.\.venv\Scripts\python.exe app.py --command "set volume to 50" --dry-run --plain
```

Run the test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Current Limitations

- Windows only
- Conversation history lasts for the current process and is not persisted yet
- Wake-word mode must be started manually unless the user configures Windows startup
- Desktop actions use deterministic rules rather than LLM-generated structured actions
- There is no tray interface yet
- YouTube video-specific controls such as play, pause, seek, and video fullscreen are not implemented
