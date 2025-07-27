#!/bin/bash

PID_FILE="$HOME/.jarvis/jarvis"
STATUS_FILE="$HOME/.jarvis/jarvis.status"
SPOKEN_FILE="$HOME/.jarvis/jarvis.spoken"
HEARD_FILE="$HOME/.jarvis/jarvis.heard"
# Get current user
CURRENT_USER=$(whoami)
# Default status
STATUS="offline"
HEARD_TOOLTIP="User: n/a"
SPOKEN_TOOLTIP="Jarvis: n/a"

# Check if PID file exists and is running
if [[ -f "$PID_FILE" ]]; then
  PID=$(<"$PID_FILE")
  if ps -p "$PID" > /dev/null 2>&1; then
    [[ -f "$STATUS_FILE" ]] && STATUS=$(<"$STATUS_FILE") || STATUS="unknown"

    if [[ -f "$HEARD_FILE" ]]; then
      LAST_HEARD=$(<"$HEARD_FILE")
      HEARD_TOOLTIP="$LAST_HEARD"
    else
      HEARD_TOOLTIP="$STATUS"
    fi

    if [[ -f "$SPOKEN_FILE" ]]; then
      LAST_SPOKEN=$(<"$SPOKEN_FILE")
      SPOKEN_TOOLTIP="$LAST_SPOKEN"
    else
      SPOKEN_TOOLTIP="$STATUS"
    fi
  fi
fi

# Icon selection
case "$STATUS" in
  speaking) ICON="󱌈" ;;
  listening) ICON="" ;;
  idle) ICON="" ;;
  canceled) ICON="󰜺" ;;
  offline|unknown) ICON="" ;;
  *) ICON="" ;;
esac

ESCAPED_HEARD=$(echo "$LAST_HEARD" | sed ':a;N;$!ba;s/\n/\\n/g' | sed 's/"/\\"/g')
ESCAPED_SPOKEN=$(echo "$LAST_SPOKEN" | sed ':a;N;$!ba;s/\n/\\n/g' | sed 's/"/\\"/g')

# Output JSON for Waybar
echo "{\"text\": \"$ICON jarvis\", \"tooltip\": \" $CURRENT_USER:\n$ESCAPED_HEARD\\n\n󱌈 jarvis:\n$ESCAPED_SPOKEN\"}"
