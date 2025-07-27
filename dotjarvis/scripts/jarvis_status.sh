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
      HEARD_TOOLTIP=" $CURRENT_USER: \n   $LAST_HEARD\n - - -"
    else
      HEARD_TOOLTIP=" $CURRENT_USER: \n   $STATUS\n - - -"
    fi

    if [[ -f "$SPOKEN_FILE" ]]; then
      LAST_SPOKEN=$(<"$SPOKEN_FILE")
      SPOKEN_TOOLTIP=" jarvis: \n   $LAST_SPOKEN\n - - -"
    else
      SPOKEN_TOOLTIP=" jarvis: \n   $STATUS\n - - -"
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

# Output JSON for Waybar
echo "{\"text\": \"$ICON jarvis\", \"tooltip\": \"$HEARD_TOOLTIP\\n\n$SPOKEN_TOOLTIP\"}"
