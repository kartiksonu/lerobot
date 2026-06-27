#!/bin/bash
# Setup VNC password for x11vnc (system service)
# Run this script to set a password for remote VNC access

echo "Setting up VNC password for system service..."
echo "Enter VNC password:"
read -s PASSWORD
echo ""
echo "Verify password:"
read -s PASSWORD_VERIFY
echo ""

if [ "$PASSWORD" != "$PASSWORD_VERIFY" ]; then
    echo "❌ Passwords do not match"
    exit 1
fi

# Install tigervnc-common if not available (provides vncpasswd)
if ! command -v vncpasswd &> /dev/null; then
    echo "Installing tigervnc-common..."
    sudo apt install -y tigervnc-common > /dev/null 2>&1
fi

# Create password file using vncpasswd
echo "$PASSWORD" | vncpasswd -f | sudo tee /etc/x11vnc.passwd > /dev/null
sudo chmod 600 /etc/x11vnc.passwd

if [ -f /etc/x11vnc.passwd ]; then
    echo ""
    echo "✅ VNC password file created at /etc/x11vnc.passwd"
    echo ""
    echo "Updating x11vnc service to use password..."
    sudo sed -i 's/-nopw/-rfbauth \/etc\/x11vnc.passwd/' /etc/systemd/system/x11vnc.service
    sudo systemctl daemon-reload
    sudo systemctl restart x11vnc.service
    echo ""
    echo "✅ Service updated and restarted. You can now connect with the password you set."
else
    echo "❌ Failed to create password file"
    exit 1
fi
