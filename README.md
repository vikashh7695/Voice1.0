# Voice Assistant

A modular Python voice assistant with three interchangeable front-ends
(console, system tray, chat-style GUI), able to launch apps and websites,
control Spotify, search the web, and answer basic questions — all packaged
into standalone Windows `.exe` files.

## Features

- Speech-to-text (Google Speech Recognition) and offline text-to-speech (pyttsx3)
- Opens desktop apps: VS Code, Notepad, Calculator, File Explorer, Command Prompt, Terminal
- Opens websites: YouTube, Google, GitHub, Gmail, or a blank browser
- Plays songs on YouTube (via `pywhatkit`) or Spotify (via the official Spotify Web API)
- Google search, Wikipedia lookups, jokes, time/date
- Three front-ends: a console app, a system-tray background app, and a
  ChatGPT-style chat window with a mic button
- All activity logged to `assistant.log` for debugging
- Packagable into standalone `.exe` files with PyInstaller

## Project structure

```
voice_assistant/
├── main.py              # Console entry point: wake word + command sessions
├── tray.py              # System-tray entry point (no console window)
├── gui.py               # Chat-window entry point (type or click mic)
├── listener.py          # Microphone input -> text (speech_recognition)
├── speaker.py            # Text -> speech (pyttsx3)
├── commands.py           # All command handlers + routing table
├── spotify_client.py     # Spotify Web API client (search + play)
├── event_bus.py          # Pub/sub so listener/speaker can notify a GUI
├── requirements.txt
├── .env.example          # Template for Spotify credentials (safe to commit)
├── .env                  # Your real Spotify credentials (gitignored)
├── .gitignore
├── build_exe.bat         # Packages main.py -> VoiceAssistant.exe
├── build_tray_exe.bat    # Packages tray.py -> VoiceAssistantTray.exe
├── build_gui_exe.bat     # Packages gui.py  -> VoiceAssistantGUI.exe
└── assistant.log         # Runtime log (created automatically)
```

## Setup

```bash
pip install -r requirements.txt
```

**PyAudio note:**
- Windows: usually installs fine via pip.
- Mac: `brew install portaudio` first, then `pip install pyaudio`.
- Linux: `sudo apt install portaudio19-dev python3-pyaudio` first.

**Python 3.12+ note:** `speech_recognition` internally imports `distutils`,
which was removed from the standard library in Python 3.12. Fix:
```bash
pip install setuptools
```
`listener.py` also imports `setuptools` before `speech_recognition` as a
safety net.

### Spotify setup (optional, only needed for "play X on spotify")

1. Go to https://developer.spotify.com/dashboard and log in (any free account works).
2. Click **Create app**. Any name/description is fine. For **Redirect URI**,
   use `http://127.0.0.1:8888/callback` — Spotify requires the literal
   loopback IP, not `localhost`, and rejects plain `http://localhost/...`
   as insecure. This URI is required by the dashboard but unused by this
   script (we only use the Client Credentials flow for searching).
3. Open the app → **Settings** → copy the **Client ID** and **Client Secret**.
4. Copy `.env.example` to a new file named `.env` and fill in your real values:
   ```
   SPOTIFY_CLIENT_ID=your-real-client-id
   SPOTIFY_CLIENT_SECRET=your-real-client-secret
   ```
   Make sure the file is actually named `.env`, not `.env.txt` (Windows
   often hides file extensions — enable "File name extensions" in File
   Explorer's View tab to check).
5. `.env` is listed in `.gitignore` — never commit or share it.

If Spotify commands fail, check `assistant.log` — it logs the exact
reason (missing credentials, rejected auth, no search results, etc.).

## Running it

### Console version
```bash
python main.py
```
Say **"hey assistant"** (or "hey python" / "wake up") to wake it, then
speak commands one after another — no need to repeat the wake word
between them. After two silences in a row it goes back to sleep. Say
"stop" / "exit" / "quit" / "stop listening" / "shut down" to close it.

### Tray version (no console window)
```bash
python tray.py
```
Runs the same assistant hidden in the system tray with a small mic
icon. Right-click → Quit, or say "stop" by voice.

### GUI version (chat window)
```bash
python gui.py
```
A dark, chat-style window. **No wake word needed here** — type a
message and hit Enter, or click the mic button to speak one command at
a time. (A continuous background listener can't safely share the
microphone with a manual mic button, so the GUI is on-demand instead
of always-listening.)

## Commands

| Say or type | Does |
|---|---|
| "what time is it" / "current time" | Speaks the current time |
| "what's today's date" / "what day is it" | Speaks the current date |
| "open vs code" / "open visual studio code" | Launches VS Code |
| "open notepad" | Launches Notepad |
| "open calculator" | Launches Calculator |
| "open file explorer" / "open explorer" | Opens File Explorer |
| "open command prompt" | Opens cmd |
| "open terminal" | Opens Windows Terminal |
| "open youtube" / "open google" / "open github" / "open gmail" | Opens that site in your browser |
| "open browser" | Opens a blank browser window |
| "play [song] on spotify" | Searches Spotify and plays the top match via the desktop app |
| "play [song/video]" | Plays it on YouTube |
| "search for [term]" | Google search |
| "who is [person]" / "what is [thing]" | Wikipedia summary (2 sentences) |
| "tell me a joke" | Random joke |
| "hey assistant" / "wake up" (in the GUI) | Friendly reminder that no wake word is needed there |
| "stop" / "exit" / "quit" / "goodbye" / "stop listening" / "shut down" | Closes the assistant |

Anything unmatched falls through to: *"I didn't understand that command."*

## Packaging into standalone .exe files

You need to be on Windows to build a Windows executable (PyInstaller
doesn't cross-compile). From inside the project folder, with PyInstaller's
scripts on your PATH:

```powershell
$env:Path += ";C:\Users\<you>\AppData\Roaming\Python\Python312\Scripts"
```

Then run whichever build script matches the front-end you want:

```powershell
.\build_exe.bat        # -> dist\VoiceAssistant.exe        (console)
.\build_tray_exe.bat   # -> dist\VoiceAssistantTray.exe    (tray, --windowed)
.\build_gui_exe.bat    # -> dist\VoiceAssistantGUI.exe     (chat GUI, --windowed)
```

**Test each exe from a terminal before relying on it**, since
`--windowed` builds show no console — if you need to debug one, remove
`--windowed` from the `.bat` file temporarily, rebuild, and run from
`cmd`/PowerShell to see any errors.

**Autostart on login:** press `Win + R` → `shell:startup` → drop a
shortcut to your chosen exe in that folder.

## Known issues already fixed (for context if you extend this)

- **`ModuleNotFoundError: distutils`** on Python 3.12+ — fixed by
  importing `setuptools` before `speech_recognition`.
- **PyInstaller onefile exe silently restarting itself** — fixed with
  `multiprocessing.freeze_support()` at the top of each entry point.
- **`pyttsx3` `RuntimeError: run loop already started`** — the SAPI5
  driver isn't thread-safe and hangs/crashes if the same engine
  instance is reused across calls. Fixed by building a fresh engine
  per `speak()` call.
- **GUI silently ignoring the first message typed** — pywebview's JS
  API bridge (`window.pywebview.api`) isn't ready the instant the
  window opens. Fixed by disabling the input until the
  `pywebviewready` event fires.
- **Short exit words ("stop", "quit") sometimes not recognized** —
  single-syllable words are inherently hard for speech recognition
  (e.g. "quit" commonly misheard as "quiet"). Mitigated with longer
  alternative phrases ("stop listening", "shut down") and by removing
  a hardcoded `energy_threshold` in favor of dynamic calibration.

## Extending it

Add a new command in two steps, inside `commands.py`:

1. Write a handler: `def my_command(query: str) -> None: speak("...")`
2. Register it in `COMMANDS`: `(["trigger phrase"], my_command)`
   (order matters — more specific triggers should come before broader ones)

## Roadmap ideas

- Weather command (API + JSON)
- Volume/media key control
- System info ("how much battery do I have")
- Reminders/alarms
- AI-powered natural language understanding via a free LLM backend
  (Ollama running locally, or Groq's free cloud API) instead of fixed
  keyword matching — a real upgrade path, parked for later