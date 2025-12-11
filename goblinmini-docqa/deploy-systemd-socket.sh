#!/bin/bash
# Goblin DocQA systemd socket activation deployment script
# This script sets up systemd socket activation for clean, atomic deployments

set -e

echo "🚀 Goblin DocQA systemd socket activation deployment"
echo "=================================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (sudo)"
   exit 1
fi

# Configuration
SERVICE_NAME="goblin-docqa"
USER_NAME="docqa"
GROUP_NAME="docqa"
INSTALL_DIR="/opt/goblinmini-docqa"
SOCKET_PATH="/run/goblinmini-docqa.sock"

echo "📋 Configuration:"
echo "   Service: $SERVICE_NAME"
echo "   User/Group: $USER_NAME/$GROUP_NAME"
echo "   Install dir: $INSTALL_DIR"
echo "   Socket: $SOCKET_PATH"
echo ""

# Create system user and group if they don't exist
if ! id "$USER_NAME" &>/dev/null; then
    echo "👤 Creating system user: $USER_NAME"
    useradd --system --shell /bin/bash --home-dir "$INSTALL_DIR" --create-home "$USER_NAME"
else
    echo "✅ User $USER_NAME already exists"
fi

if ! getent group "$GROUP_NAME" &>/dev/null; then
    echo "👥 Creating system group: $GROUP_NAME"
    groupadd --system "$GROUP_NAME"
else
    echo "✅ Group $GROUP_NAME already exists"
fi

# Add user to group if not already
if ! groups "$USER_NAME" | grep -q "$GROUP_NAME"; then
    echo "🔗 Adding $USER_NAME to $GROUP_NAME group"
    usermod -a -G "$GROUP_NAME" "$USER_NAME"
fi

# Create installation directory
echo "📁 Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
chown "$USER_NAME:$GROUP_NAME" "$INSTALL_DIR"

# Copy application files (assuming we're running from the project root)
if [[ -d "app" ]] && [[ -d "systemd" ]]; then
    echo "📋 Copying application files..."
    cp -r app/ "$INSTALL_DIR/"
    cp requirements.txt pyproject.toml .env.example "$INSTALL_DIR/" 2>/dev/null || true
    chown -R "$USER_NAME:$GROUP_NAME" "$INSTALL_DIR"
else
    echo "⚠️  Warning: Application files not found in current directory"
    echo "   Make sure you're running this from the project root"
fi

# Copy systemd unit files
echo "🔧 Installing systemd unit files..."
SYSTEMD_DIR="/etc/systemd/system"

cp "systemd/goblin-docqa.socket" "$SYSTEMD_DIR/"
cp "systemd/goblin-docqa.service" "$SYSTEMD_DIR/"
cp "systemd/goblin-docqa-worker.service" "$SYSTEMD_DIR/"

# Set proper permissions
chmod 644 "$SYSTEMD_DIR/goblin-docqa.socket"
chmod 644 "$SYSTEMD_DIR/goblin-docqa.service"
chmod 644 "$SYSTEMD_DIR/goblin-docqa-worker.service"

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Enable socket (this will start on-demand)
echo "🔌 Enabling socket activation..."
systemctl enable "$SERVICE_NAME.socket"

# Create allowed directory for file uploads
ALLOWED_DIR="/mnt/allowed"
if [[ ! -d "$ALLOWED_DIR" ]]; then
    echo "📁 Creating allowed directory: $ALLOWED_DIR"
    mkdir -p "$ALLOWED_DIR"
    chown "$USER_NAME:$GROUP_NAME" "$ALLOWED_DIR"
    chmod 755 "$ALLOWED_DIR"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Configure your environment in $INSTALL_DIR/.env"
echo "2. Install Python dependencies: cd $INSTALL_DIR && pip install -r requirements.txt"
echo "3. Start the socket: sudo systemctl start $SERVICE_NAME.socket"
echo "4. Check socket status: sudo ss -l | grep goblinmini-docqa.sock"
echo "5. View logs: sudo journalctl -u $SERVICE_NAME.service -f"
echo ""
echo "🔒 Security notes:"
echo "- The service runs as unprivileged user $USER_NAME"
echo "- Socket activation prevents port conflicts"
echo "- systemd manages process lifecycle and restarts"
echo ""
echo "🧪 Testing:"
echo "# Check socket is listening"
echo "sudo ss -l | grep goblinmini-docqa.sock"
echo ""
echo "# Test connection (replace with your token)"
echo "curl -s -H 'Authorization: Bearer YOUR_TOKEN' --unix-socket /run/goblinmini-docqa.sock http://localhost/health"
