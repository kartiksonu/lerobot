#!/bin/bash
# Setup VNC password for x11vnc
# Run this script to set a password for remote VNC access

echo "Setting up VNC password..."
echo "You will be prompted to enter a password (twice for confirmation)"
echo ""

x11vnc -storepasswd ~/.vnc/passwd

if [ -f ~/.vnc/passwd ]; then
    echo ""
    echo "✅ VNC password file created at ~/.vnc/passwd"
    echo ""
    echo "To enable password protection, update the x11vnc service:"
    echo "  Edit ~/.config/systemd/user/x11vnc.service"
    echo "  Add: -rfbauth %h/.vnc/passwd"
    echo "  Remove: -nopw (if present)"
    echo "  Then: systemctl --user daemon-reload && systemctl --user restart x11vnc"
else
    echo "❌ Failed to create password file"
    exit 1
fi
