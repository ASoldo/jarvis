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
