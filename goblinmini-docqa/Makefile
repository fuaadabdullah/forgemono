.PHONY: build up test lint run rotate-token server server-bg stop-server status clean-locks deploy deploy-systemd deploy-docker

build:
	docker build -t goblin/docqa:local .

up:
	docker compose -f docker/docker-compose.yml up --build

run:
	python -m app.cli --help

test:
	pytest -q

lint:
	python -m pip install -r requirements-dev.txt
 	# Ruff checks (linting)
 	ruff check .
 	# isort checks
 	isort --check-only .
 	# black checks
 	black --check .

fmt:
 	python -m pip install -r requirements-dev.txt
 	# Format with isort + black + ruff autofix
 	isort .
 	black .
 	ruff format .

rotate-token:
	@echo "🔄 Generating new secure token..."
	@echo "New DOCQA_TOKEN: $$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")"
	@echo ""
	@echo "📋 Token Rotation Steps:"
	@echo "1. Copy the new token above"
	@echo "2. Update your .env file: DOCQA_TOKEN=<new-token>"
	@echo "3. Restart all containers: make up"
	@echo "4. Update SECURITY.md with rotation date"
	@echo "5. Remove old tokens from all storage"
	@echo ""
	@echo "⚠️  WARNING: This will invalidate all existing API tokens!"

# Single instance deployment targets
deploy:
	@echo "🚀 Goblin Mini DocQA Single Instance Deployment"
	@echo "=============================================="
	@echo "Choose deployment method:"
	@echo "1) systemd (bare metal) - make deploy-systemd"
	@echo "2) Docker Compose - make deploy-docker"
	@echo ""
	@echo "Both methods prevent multiple instances and include resource limits."

deploy-systemd:
	@echo "🔧 Deploying with systemd (single instance)..."
	./deploy.sh
	@echo "1" | ./deploy.sh

deploy-docker:
	@echo "🐳 Deploying with Docker Compose (single instance)..."
	./deploy.sh
	@echo "2" | ./deploy.sh

# Supervisor-style targets for preventing ghost processes
server:
	@echo "🚀 Starting Goblin Mini DocQA server with supervision..."
	@echo "📋 Deployment: Single listener rule (1 worker) - no model duplication"
	@./utils/check_port.sh $$(grep DOCQA_PORT .env | cut -d'=' -f2) && \
	PYTHONPATH=/Users/fuaadabdullah/ForgeMonorepo/goblinmini-docqa python3 -m uvicorn app.server:app --host 0.0.0.0 --port $$(grep DOCQA_PORT .env | cut -d'=' -f2) --workers 1 --reload

server-bg:
	@echo "🚀 Starting Goblin Mini DocQA server in background..."
	@echo "📋 Deployment: Single listener rule (1 worker) - no model duplication"
	@./utils/check_port.sh $$(grep DOCQA_PORT .env | cut -d'=' -f2) && \
	PYTHONPATH=/Users/fuaadabdullah/ForgeMonorepo/goblinmini-docqa nohup python3 -m uvicorn app.server:app --host 0.0.0.0 --port $$(grep DOCQA_PORT .env | cut -d'=' -f2) --workers 1 > server.log 2>&1 & \
	echo $$! > server.pid && \
	echo "✅ Server started with PID: $$(cat server.pid)" && \
	echo "📝 Logs: server.log" && \
	echo "🛑 To stop: make stop-server"

stop-server:
	@if [ -f server.pid ]; then \
		echo "🛑 Stopping server (PID: $$(cat server.pid))..."; \
		kill $$(cat server.pid) 2>/dev/null || true; \
		rm -f server.pid; \
		echo "✅ Server stopped"; \
	else \
		echo "⚠️  No server PID file found"; \
	fi

status:
	@if [ -f server.pid ] && kill -0 $$(cat server.pid) 2>/dev/null; then \
		echo "✅ Server is running (PID: $$(cat server.pid))"; \
		echo "🌐 Port: $$(grep DOCQA_PORT .env | cut -d'=' -f2)"; \
	else \
		echo "❌ Server is not running"; \
		rm -f server.pid 2>/dev/null || true; \
	fi

clean-locks:
	@echo "🧹 Cleaning up lockfiles..."
	@rm -rf /tmp/goblinmini-docqa/
	@echo "✅ Lockfiles cleaned"
