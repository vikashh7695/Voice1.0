"""
gui.py
Chat-style GUI for the voice assistant, similar to a ChatGPT window,
built with pywebview. Type a message, or click the mic button to speak
one command at a time - no wake word needed here, since a continuous
background listener would fight the manual mic button for the same
microphone.

Usage:
    python gui.py
"""

import multiprocessing
import queue
import threading

import webview

import event_bus
from commands import handle_command
from listener import listen, calibrate

window = None          # set in main()
_calibrated_once = False
task_queue: "queue.Queue" = queue.Queue()

HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  :root {
    --bg: #05070c;
    --panel: rgba(255,255,255,0.045);
    --border: rgba(255,255,255,0.09);
    --accent: #5082ff;
    --accent2: #7c5cff;
    --text: #e7e9ee;
    --muted: #838aa0;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; height: 100%;
    background: radial-gradient(circle at top, #131a2c 0%, #05070c 65%);
    font-family: "Segoe UI", system-ui, sans-serif;
    color: var(--text);
    overflow: hidden;
  }
  body { display: flex; flex-direction: column; }

  header {
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }
  .dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: var(--muted);
    transition: background .25s, box-shadow .25s;
    flex-shrink: 0;
  }
  .dot.listening {
    background: var(--accent);
    box-shadow: 0 0 10px 2px rgba(80,130,255,0.7);
    animation: pulse 1.1s infinite;
  }
  .dot.speaking {
    background: var(--accent2);
    box-shadow: 0 0 10px 2px rgba(124,92,255,0.7);
  }
  @keyframes pulse {
    0%   { transform: scale(1);   opacity: 1; }
    50%  { transform: scale(1.5); opacity: .55; }
    100% { transform: scale(1);   opacity: 1; }
  }
  header h1 { font-size: 14px; font-weight: 600; margin: 0; letter-spacing: .02em; }
  #status { font-size: 12px; color: var(--muted); margin-left: auto; }

  #log {
    flex: 1;
    overflow-y: auto;
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .msg {
    max-width: 80%;
    padding: 10px 14px;
    border-radius: 14px;
    font-size: 13.5px;
    line-height: 1.45;
    border: 1px solid var(--border);
    background: var(--panel);
    backdrop-filter: blur(12px);
    animation: rise .22s ease-out;
    word-wrap: break-word;
  }
  @keyframes rise {
    from { transform: translateY(6px); opacity: 0; }
    to   { transform: translateY(0);   opacity: 1; }
  }
  .msg.user {
    align-self: flex-end;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border: none;
    color: white;
  }
  .msg.assistant { align-self: flex-start; }
  .msg .label {
    display: block;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: var(--muted);
    margin-bottom: 3px;
  }
  .msg.user .label { color: rgba(255,255,255,0.75); }

  #empty {
    margin: auto;
    text-align: center;
    color: var(--muted);
    font-size: 13px;
  }

  ::-webkit-scrollbar { width: 7px; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

  /* ---- input bar, always pinned to the bottom ---- */
  #inputbar {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 14px;
    border-top: 1px solid var(--border);
    background: rgba(255,255,255,0.02);
  }
  #textinput {
    flex: 1;
    background: rgba(255,255,255,0.06);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 10px 16px;
    color: var(--text);
    font-size: 13.5px;
    outline: none;
  }
  #textinput:focus { border-color: var(--accent); }
  #textinput::placeholder { color: var(--muted); }

  .iconbtn {
    width: 38px; height: 38px;
    border-radius: 50%;
    border: 1px solid var(--border);
    background: rgba(255,255,255,0.06);
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    transition: background .15s, transform .1s;
    color: var(--text);
  }
  .iconbtn:hover { background: rgba(255,255,255,0.12); }
  .iconbtn:active { transform: scale(0.94); }

  #sendbtn {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border: none;
  }

  #micbtn.recording {
    background: var(--accent);
    box-shadow: 0 0 12px 3px rgba(80,130,255,0.7);
    animation: pulse 1.1s infinite;
  }
  #micbtn.disabled { opacity: 0.5; pointer-events: none; }
</style>
</head>
<body>
  <header>
    <div class="dot" id="dot"></div>
    <h1>Voice Assistant</h1>
    <div id="status">Idle</div>
  </header>

  <div id="log">
    <div id="empty">Type a message or tap the mic to speak</div>
  </div>

  <div id="inputbar">
    <div class="iconbtn disabled" id="micbtn" title="Speak a command">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
        <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3z" stroke="currentColor" stroke-width="1.8"/>
        <path d="M19 11a7 7 0 0 1-14 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        <path d="M12 18v3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
    </div>
    <input id="textinput" type="text" placeholder="Connecting..." autocomplete="off" disabled />
    <div class="iconbtn" id="sendbtn" title="Send">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M4 12l16-8-6 8 6 8-16-8z" fill="white"/>
      </svg>
    </div>
  </div>

  <script>
    function addMessage(sender, text) {
      const empty = document.getElementById('empty');
      if (empty) empty.remove();

      const log = document.getElementById('log');
      const div = document.createElement('div');
      div.className = 'msg ' + sender;
      const label = document.createElement('span');
      label.className = 'label';
      label.textContent = sender === 'user' ? 'You' : 'Assistant';
      div.appendChild(label);
      div.appendChild(document.createTextNode(text));
      log.appendChild(div);
      log.scrollTop = log.scrollHeight;
    }

    function setStatus(state) {
      const dot = document.getElementById('dot');
      const status = document.getElementById('status');
      const mic = document.getElementById('micbtn');
      dot.className = 'dot' + (state === 'listening' || state === 'speaking' ? ' ' + state : '');
      status.textContent =
        state === 'listening' ? 'Listening...' :
        state === 'speaking'  ? 'Speaking...'  : 'Idle';

      if (state === 'listening') {
        mic.classList.add('recording');
        mic.classList.add('disabled');
      } else {
        mic.classList.remove('recording');
        mic.classList.remove('disabled');
      }
    }

    function sendTyped() {
      const input = document.getElementById('textinput');
      const text = input.value.trim();
      if (!text || !window.pywebview) return;
      input.value = '';
      window.pywebview.api.send_text(text);
    }

    document.getElementById('sendbtn').addEventListener('click', sendTyped);
    document.getElementById('textinput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') sendTyped();
    });
    document.getElementById('micbtn').addEventListener('click', () => {
      if (!window.pywebview) return;
      window.pywebview.api.start_voice_input();
    });

    // window.pywebview.api isn't wired up the instant the page loads -
    // pywebview fires this event once the bridge is actually ready.
    // Typing before that would otherwise fail silently.
    window.addEventListener('pywebviewready', function () {
      const input = document.getElementById('textinput');
      input.disabled = false;
      input.placeholder = 'Type a command...';
      document.getElementById('micbtn').classList.remove('disabled');
    });
  </script>
</body>
</html>
"""


class Api:
    """Methods callable from JS as window.pywebview.api.<name>(...).
    Both just enqueue work - a single worker thread (started in main())
    processes one item at a time, so pyttsx3 (which is not thread-safe
    and breaks if called concurrently) only ever gets called from one
    thread, in order."""

    def send_text(self, text: str) -> bool:
        text = (text or "").strip()
        if text:
            task_queue.put(("text", text))
        return True

    def start_voice_input(self) -> bool:
        task_queue.put(("voice", None))
        return True


def _process_text(text: str) -> None:
    event_bus.emit("user", text)
    handle_command(text.lower())


def _process_voice() -> None:
    global _calibrated_once
    if not _calibrated_once:
        calibrate()
        _calibrated_once = True

    text = listen(phrase_time_limit=6)  # listener.py already emits
    # the "user" event and listening/idle status for us
    if text:
        handle_command(text)


def worker_loop() -> None:
    """Single consumer for task_queue. Runs every command one at a time,
    so speak() is never called from two threads at once."""
    while True:
        kind, payload = task_queue.get()
        try:
            if kind == "text":
                _process_text(payload)
            elif kind == "voice":
                _process_voice()
        except SystemExit:
            if window is not None:
                window.destroy()
            break
        except Exception as e:
            # Don't let one bad command kill the worker thread - log it
            # and keep processing future commands.
            print(f"Command handling error: {e}")
        finally:
            task_queue.task_done()


def register_event_forwarding() -> None:
    def on_event(kind: str, payload: str) -> None:
        if window is None:
            return
        if kind in ("user", "assistant"):
            safe_text = (
                payload.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
            )
            window.evaluate_js(f"addMessage('{kind}', '{safe_text}')")
        elif kind == "status":
            window.evaluate_js(f"setStatus('{payload}')")

    event_bus.subscribe(on_event)


def main() -> None:
    global window

    window = webview.create_window(
        "Voice Assistant",
        html=HTML,
        js_api=Api(),
        width=420,
        height=640,
        background_color="#05070c",
    )

    register_event_forwarding()
    threading.Thread(target=worker_loop, daemon=True).start()
    webview.start()


if __name__ == "__main__":
    # Prevents the packaged .exe from re-launching itself as a subprocess
    # on Windows (same reasoning as in main.py / tray.py).
    multiprocessing.freeze_support()
    main()