<img width="249" height="26" alt="image" src="https://github.com/user-attachments/assets/2f252363-7c44-40e3-8870-c5adeb606e5e" />

# 🧠 Jarvis – Local Voice-Controlled AI Assistant

**Jarvis** is a voice-activated, conversational AI assistant powered by a local LLM (Qwen via Ollama). It listens for a wake word, processes spoken commands using a local language model with LangChain, and responds out loud via TTS. It supports tool-calling for dynamic functions like checking the current time.

---

## Features

* Voice-activated with wake word **"Jarvis"**
* Local language model (Qwen 3 via Ollama)
* Tool-calling with LangChain
* Text-to-speech responses via `pyttsx3`
* Example tool: Get the current time in a given city
* Optional support for OpenAI API integration

---

## ▶️ How It Works (`main.py`)

1. **Startup & local LLM Setup**

   * Initializes a local Ollama model (`qwen3:1.7b`) via `ChatOllama`
   * Registers tools (`get_time`) using LangChain

2. **Wake Word Listening**

   * Listens via microphone (e.g., `device_index=0`)
   * If it hears the word **"Jarvis"**, it enters "conversation mode"

3. **Voice Command Handling**

   * Records the user’s spoken command
   * Passes the command to the LLM, which may invoke tools
   * Responds using `pyttsx3` text-to-speech (with optional custom voice)

4. **Timeout**

   * If the user is inactive for more than 30 seconds in conversation mode, it resets to wait for the wake word again.

---

## 📁 Directory Structure

```
~/.jarvis/
├── jarvis              # PID of running process
├── jarvis.status       # Status indicator (idle, listening, speaking, canceled)
├── jarvis.spoken       # Status indicator for tooltip (last spoken text)
└── scripts/
    ├── jarvis_status.sh
    └── cancel_tts.sh
```

---

## 📟 Waybar Integration

### Waybar Module Setup

Update your Waybar `config.jsonc`:

```jsonc
"custom/jarvis": {
  "format": "{}",
  "return-type": "json",
  "interval": 1,
  "exec": "~/.jarvis/scripts/jarvis_status.sh",
  "on-click": "~/.jarvis/scripts/cancel_tts.sh",
  "tooltip": true
}
```

### `jarvis_status.sh`

```bash
#!/bin/bash

PID_FILE="$HOME/.jarvis/jarvis"
STATUS_FILE="$HOME/.jarvis/jarvis.status"
SPOKEN_FILE="$HOME/.jarvis/jarvis.spoken"

# Default status
STATUS="offline"
TOOLTIP="Jarvis: offline"

# Check if PID file exists and is running
if [[ -f "$PID_FILE" ]]; then
  PID=$(cat "$PID_FILE")
  if ps -p "$PID" > /dev/null 2>&1; then
    # If running, check status file
    if [[ -f "$STATUS_FILE" ]]; then
      STATUS=$(cat "$STATUS_FILE")
    else
      STATUS="unknown"
    fi

    # Use spoken text if available for tooltip
    if [[ -f "$SPOKEN_FILE" ]]; then
      LAST_SPOKEN=$(<"$SPOKEN_FILE")
      TOOLTIP="Jarvis: $LAST_SPOKEN"
    else
      TOOLTIP="Jarvis: $STATUS"
    fi
  fi
fi

case "$STATUS" in
  speaking)
    ICON="󱌈"
    ;;
  listening)
    ICON=""
    ;;
  idle)
    ICON=""
    ;;
  canceled)
    ICON="󰜺"
    ;;
  offline|unknown)
    ICON=""
    ;;
  *)
    ICON=""
    ;;
esac

echo "{\"text\": \"$ICON jarvis\", \"tooltip\": \"$TOOLTIP\"}"

```

### `cancel_tts.sh`

```bash
#!/bin/bash
STATUS_FILE="$HOME/.jarvis/jarvis.status"
echo "canceled" > "$STATUS_FILE"
notify-send "Jarvis: speaking canceled"
```

Make sure to set permissions:

```bash
chmod +x ~/.jarvis/scripts/*.sh
```

---

## 🧠 Python Integration

Ensure your Python script creates the `.jarvis` and `.jarvis.status` files and handles signals:

```python
import os, signal
PID_FILE = os.path.expanduser("~/.jarvis/jarvis")
STATUS_FILE = os.path.expanduser("~/.jarvis/jarvis.status")

def update_status(state):
    with open(STATUS_FILE, "w") as f:
        f.write(state)

def handle_sigusr1(signum, frame):
    update_status("idle")
    print("[SIGUSR1] TTS canceled")

signal.signal(signal.SIGUSR1, handle_sigusr1)

with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))
```

---

## 🧩 Waybar Autostart (User Service)

Waybar should not be run as a system service. Instead, enable it for the user:

```bash
systemctl --user enable --now waybar.service
```

If needed, add this to Hyprland’s autostart or your `.zprofile`:

```sh
exec --no-startup-id systemctl --user start waybar.service
```

You can verify Waybar is installed as a user service:

```bash
ls /usr/lib/systemd/user/waybar.service
```

---

## Convert to `--user` systemd service (as expected for audio apps)

### 1. Move the service file to user systemd directory

Create the file:

```bash
mkdir -p ~/.config/systemd/user
nano ~/.config/systemd/user/jarvis.service
```

Paste this user-level service:

```ini
[Unit]
Description=Jarvis Voice Assistant
After=sound.target default.target

[Service]
Type=simple
WorkingDirectory=/home/rootster/Documents/jarvis
ExecStart=/home/rootster/Documents/jarvis/start-jarvis.sh
Restart=always
Environment=RHVOICE_BIN=/snap/bin/rhvoice.test
Environment=PULSE_SERVER=unix:/run/user/1000/pulse/native

[Install]
WantedBy=default.target
```

> Replace `start-jarvis.sh` with `python main.py` directly if you're not using a wrapper script.

### 2. Enable and start the user service

```bash
systemctl --user daemon-reload
systemctl --user enable jarvis.service
systemctl --user start jarvis.service
```

### 3. Verify it's running properly

```bash
journalctl --user -u jarvis.service -f
```


## ✅ Final Notes

* Icons use Nerd Font glyphs, ensure your terminal/Waybar uses `CaskaydiaMono Nerd Font` or similar
* Emoji support for fallback (`Noto Color Emoji` font)
* Compatible with Alacritty, Kitty, and other emoji-enabled terminals

---

If you'd like an install script to bootstrap `.jarvis`, dependencies, and Waybar setup—just ask!
