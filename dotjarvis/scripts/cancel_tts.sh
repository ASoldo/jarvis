#!/bin/bash
STATUS_FILE="$HOME/.jarvis/jarvis.status"
echo "canceled" > "$STATUS_FILE"
notify-send "Jarvis: speaking canceled"
