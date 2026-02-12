#!/bin/bash
# Goblin Mini DocQA - Single Instance Deployment Script
# Prevents multiple listeners and sets resource limits

set -e

echo "🚀 Goblin Mini DocQA Single Instance Deployment"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/goblinmini-docqa"
SERVICE_NAME="goblinmini-docqa"
WORKER_SERVICE_NAME="goblinmini-docqa-worker"
USER="docqa"

error() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠️  Warning: $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    error "Do not run this script as root. It will use sudo when needed."
fi

echo "📋 Deployment Type Selection:"
echo "1) systemd (bare metal)"
echo "2) Docker Compose"
read -p "Choose deployment type [1-2]: " DEPLOY_TYPE

case $DEPLOY_TYPE in
    1)
        echo "🔧 Setting up systemd deployment..."

        # Check if systemd is available
        if ! command -v systemctl >/dev/null 2>&1; then
            error "systemd is not available on this system"
        fi

        # Create user if it doesn't exist
        if ! id "$USER" >/dev/null 2>&1; then
            echo "👤 Creating user $USER..."
            sudo useradd --system --shell /bin/bash --home-dir "$APP_DIR" --create-home "$USER" || error "Failed to create user"
        fi

        # Create application directory
        echo "📁 Creating application directory..."
        sudo mkdir -p "$APP_DIR" || error "Failed to create app directory"
        sudo chown "$USER:$USER" "$APP_DIR" || error "Failed to set ownership"

        # Copy files
        echo "📋 Copying application files..."
        sudo cp -r . "$APP_DIR/" || error "Failed to copy files"
        cd "$APP_DIR"

        # Setup virtual environment
        echo "🐍 Setting up Python virtual environment..."
        sudo -u "$USER" python3 -m venv venv || error "Failed to create venv"
        sudo -u "$USER" venv/bin/pip install --upgrade pip || error "Failed to upgrade pip"
        sudo -u "$USER" venv/bin/pip install -r requirements.txt || error "Failed to install requirements"

        # Copy environment file
        if [ ! -f ".env" ]; then
            if [ -f ".env.example" ]; then
                sudo -u "$USER" cp .env.example .env
                warning "Please edit $APP_DIR/.env with your configuration"
            else
                error ".env file not found. Please create one."
            fi
        fi

        # Install systemd services
        echo "⚙️  Installing systemd services..."
        sudo cp systemd/*.service /etc/systemd/system/ || error "Failed to copy service files"
        sudo systemctl daemon-reload || error "Failed to reload systemd"

        # Create runtime directories
        echo "📁 Creating runtime directories..."
        sudo mkdir -p /run/goblinmini-docqa || error "Failed to create runtime dir"
        sudo chown "$USER:$USER" /run/goblinmini-docqa || error "Failed to set ownership"

        # Enable and start services
        echo "🚀 Starting services..."
        sudo systemctl enable "$SERVICE_NAME" || error "Failed to enable main service"
        sudo systemctl enable "$WORKER_SERVICE_NAME" || error "Failed to enable worker service"
        sudo systemctl start "$SERVICE_NAME" || error "Failed to start main service"
        sudo systemctl start "$WORKER_SERVICE_NAME" || error "Failed to start worker service"

        # Verify services
        echo "🔍 Verifying deployment..."
        sleep 3
        if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
            success "Main service is running"
        else
            error "Main service failed to start"
        fi

        if sudo systemctl is-active --quiet "$WORKER_SERVICE_NAME"; then
            success "Worker service is running"
        else
            error "Worker service failed to start"
        fi

        echo ""
        success "systemd deployment completed!"
        echo "📊 Management commands:"
        echo "  sudo systemctl status $SERVICE_NAME"
        echo "  sudo systemctl status $WORKER_SERVICE_NAME"
        echo "  sudo journalctl -u $SERVICE_NAME -f"
        echo "  sudo journalctl -u $WORKER_SERVICE_NAME -f"

        ;;
    2)
        echo "🐳 Setting up Docker Compose deployment..."

        # Check if docker and docker-compose are available
        if ! command -v docker >/dev/null 2>&1; then
            error "Docker is not installed"
        fi

        if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
            error "Docker Compose is not available"
        fi

        # Check for .env file
        if [ ! -f ".env" ]; then
            if [ -f ".env.example" ]; then
                cp .env.example .env
                warning "Please edit .env with your configuration before starting"
            else
                error ".env file not found. Please create one."
            fi
        fi

        cd docker

        # Start services
        echo "🚀 Starting Docker services..."
        if command -v docker-compose >/dev/null 2>&1; then
            docker-compose up -d || error "Failed to start services with docker-compose"
        else
            docker compose up -d || error "Failed to start services with docker compose"
        fi

        # Verify services
        echo "🔍 Verifying deployment..."
        sleep 5

        if docker ps | grep -q "docqa"; then
            success "Main service container is running"
        else
            error "Main service container failed to start"
        fi

        if docker ps | grep -q "worker"; then
            success "Worker service container is running"
        else
            error "Worker service container failed to start"
        fi

        if docker ps | grep -q "redis"; then
            success "Redis service container is running"
        else
            error "Redis service container failed to start"
        fi

        echo ""
        success "Docker Compose deployment completed!"
        echo "📊 Management commands:"
        echo "  docker compose ps"
        echo "  docker compose logs -f docqa"
        echo "  docker compose logs -f worker"
        echo "  docker stats"
        echo "  docker compose down"

        ;;
    *)
        error "Invalid deployment type selected"
        ;;
esac

echo ""
echo "🔒 Single Instance Protection:"
echo "  - systemd: PID files and file locking prevent multiple instances"
echo "  - Docker: Explicit replicas: 1 prevents scaling"
echo ""
echo "🛡️  Resource Limits:"
echo "  - Main app: 4GB RAM, 2 CPU cores"
echo "  - Worker: 2GB RAM, 1 CPU core"
echo "  - Redis: 512MB RAM, 0.5 CPU cores"
echo ""
echo "📝 Next steps:"
echo "  1. Configure your .env file with proper tokens"
echo "  2. Test the API: curl http://localhost:8000/health"
echo "  3. Monitor logs for any issues"
echo "  4. Set up monitoring and alerts"
