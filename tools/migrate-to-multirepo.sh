#!/bin/bash
# Multi-Repo Migration Automation Script
# Creates all 5 repositories with proper structure

set -e  # Exit on error

MONOREPO_PATH="/Users/fuaadabdullah/ForgeMonorepo"
WORKSPACE_ROOT="/Users/fuaadabdullah"
GITHUB_USER="fuaadabdullah"

echo "🚀 Goblin Assistant Multi-Repo Migration"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Create GitHub repositories
echo -e "${YELLOW}Step 1: Creating GitHub repositories...${NC}"
read -p "Have you created the 5 GitHub repos? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please create these repos on GitHub first:"
    echo "  - goblin-assistant-backend"
    echo "  - goblin-assistant-frontend"
    echo "  - goblin-assistant-infra"
    echo "  - goblin-assistant-dev"
    echo "  - goblin-contracts"
    echo ""
    echo "Run: gh repo create fuaadabdullah/REPO_NAME --public"
    exit 1
fi

# Step 2: Extract Backend
echo -e "${GREEN}Step 2: Extracting backend repository...${NC}"
cd "$WORKSPACE_ROOT"
rm -rf goblin-assistant-backend
mkdir -p goblin-assistant-backend
cd goblin-assistant-backend
git init

echo "Copying backend files..."
cp -r "$MONOREPO_PATH/apps/goblin-assistant/backend/"* .
cp -r "$MONOREPO_PATH/apps/goblin-assistant/api" .
cp "$MONOREPO_PATH/apps/goblin-assistant/Dockerfile" .
cp "$MONOREPO_PATH/apps/goblin-assistant/requirements.txt" .

# Copy tests
if [ -d "$MONOREPO_PATH/apps/goblin-assistant/tests" ]; then
    cp -r "$MONOREPO_PATH/apps/goblin-assistant/tests" .
fi

# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.env
.env.local
*.log
.DS_Store
goblin_assistant.db
*.sqlite3
EOF

# Create README
cat > README.md << 'EOF'
# Goblin Assistant Backend

FastAPI-based backend for the Goblin Assistant AI development tool.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python start_server.py

# Run with Docker
docker build -t goblin-backend .
docker run -p 8001:8001 goblin-backend
```

## API Documentation

Once running, visit: http://localhost:8001/docs

## Environment Variables

Copy `.env.example` to `.env` and configure:
- `DATABASE_URL`
- `OPENAI_API_KEY`
- `GROQ_API_KEY`

## Testing

```bash
pytest tests/
```

## Deployment

See `.github/workflows/deploy.yml` for CI/CD pipeline.
EOF

# Create pyproject.toml
cat > pyproject.toml << 'EOF'
[project]
name = "goblin-assistant-backend"
version = "1.0.0"
description = "Goblin Assistant API"
requires-python = ">=3.11"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"
EOF

git add .
git commit -m "Initial backend extraction from monorepo"
git branch -M main
git remote add origin "git@github.com:$GITHUB_USER/goblin-assistant-backend.git"

echo -e "${GREEN}✅ Backend repository created${NC}"

# Step 3: Extract Frontend
echo -e "${GREEN}Step 3: Extracting frontend repository...${NC}"
cd "$WORKSPACE_ROOT"
rm -rf goblin-assistant-frontend
mkdir -p goblin-assistant-frontend
cd goblin-assistant-frontend
git init

echo "Copying frontend files..."
cp -r "$MONOREPO_PATH/apps/goblin-assistant/src" .
cp -r "$MONOREPO_PATH/apps/goblin-assistant/public" .
cp -r "$MONOREPO_PATH/apps/goblin-assistant/.storybook" .
cp "$MONOREPO_PATH/apps/goblin-assistant/package.json" .
cp "$MONOREPO_PATH/apps/goblin-assistant/tsconfig.json" .
cp "$MONOREPO_PATH/apps/goblin-assistant/tsconfig.node.json" .
cp "$MONOREPO_PATH/apps/goblin-assistant/vite.config.ts" .
cp "$MONOREPO_PATH/apps/goblin-assistant/vitest.config.ts" .
cp "$MONOREPO_PATH/apps/goblin-assistant/index.html" .
cp "$MONOREPO_PATH/apps/goblin-assistant/vercel.json" .
cp "$MONOREPO_PATH/apps/goblin-assistant/.env.example" .

# Copy test files
if [ -d "$MONOREPO_PATH/apps/goblin-assistant/src" ]; then
    # Tests are colocated with components
    echo "Tests are colocated in src/"
fi

# Create .gitignore
cat > .gitignore << 'EOF'
node_modules/
dist/
.env
.env.local
.env.production
.vercel
.storybook-cache
storybook-static/
coverage/
*.log
.DS_Store
EOF

# Create README
cat > README.md << 'EOF'
# Goblin Assistant Frontend

React + TypeScript frontend for Goblin Assistant.

## Quick Start

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Run Storybook
npm run storybook
```

## Environment Variables

Copy `.env.example` to `.env.local`:
- `VITE_API_URL` - Backend API URL

## Testing

- Unit tests: `npm test`
- Visual regression: `npm run chromatic`
- Storybook: `npm run storybook`

## Deployment

Deployed to Vercel via GitHub Actions. See `.github/workflows/deploy-vercel.yml`.
EOF

git add .
git commit -m "Initial frontend extraction from monorepo"
git branch -M main
git remote add origin "git@github.com:$GITHUB_USER/goblin-assistant-frontend.git"

echo -e "${GREEN}✅ Frontend repository created${NC}"

# Step 4: Create Infrastructure Repository
echo -e "${GREEN}Step 4: Creating infrastructure repository...${NC}"
cd "$WORKSPACE_ROOT"
rm -rf goblin-assistant-infra
mkdir -p goblin-assistant-infra
cd goblin-assistant-infra
git init

mkdir -p terraform/{backend,frontend,shared}
mkdir -p k8s
mkdir -p scripts

# Copy existing infra if available
if [ -d "$MONOREPO_PATH/apps/goblin-assistant/infra" ]; then
    cp -r "$MONOREPO_PATH/apps/goblin-assistant/infra/"* .
fi

# Create basic terraform structure
cat > terraform/backend/main.tf << 'EOF'
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "goblin-assistant-terraform-state"
    key    = "backend/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# Backend infrastructure (ECS, RDS, etc.)
# Add your specific infrastructure here
EOF

# Create README
cat > README.md << 'EOF'
# Goblin Assistant Infrastructure

Infrastructure as Code for Goblin Assistant using Terraform and Kubernetes.

## Structure

- `terraform/` - Terraform configurations
  - `backend/` - Backend infrastructure (ECS, RDS, ElastiCache)
  - `frontend/` - Frontend infrastructure (S3, CloudFront)
  - `shared/` - Shared resources (VPC, IAM, Secrets Manager)
- `k8s/` - Kubernetes manifests (optional)
- `scripts/` - Deployment automation scripts

## Usage

```bash
# Initialize Terraform
cd terraform/backend
terraform init

# Plan changes
terraform plan

# Apply changes
terraform apply

# Deploy via script
./scripts/deploy-backend.sh production
```

## Requirements

- Terraform >= 1.0
- AWS CLI configured
- kubectl (for K8s deployments)

## Secrets Management

Secrets are stored in AWS Secrets Manager and referenced in Terraform.
EOF

git add .
git commit -m "Initial infrastructure repository"
git branch -M main
git remote add origin "git@github.com:$GITHUB_USER/goblin-assistant-infra.git"

echo -e "${GREEN}✅ Infrastructure repository created${NC}"

# Step 5: Create Dev Repository
echo -e "${GREEN}Step 5: Creating dev orchestration repository...${NC}"
cd "$WORKSPACE_ROOT"
rm -rf goblin-assistant-dev
mkdir -p goblin-assistant-dev
cd goblin-assistant-dev
git init

mkdir -p scripts

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    image: ghcr.io/fuaadabdullah/goblin-assistant-backend:latest
    build:
      context: ../goblin-assistant-backend
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - ENV=development
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/goblin_assistant
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ../goblin-assistant-backend:/app
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  frontend:
    image: node:20-alpine
    working_dir: /app
    command: npm run dev
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8001
    volumes:
      - ../goblin-assistant-frontend:/app
      - /app/node_modules
    depends_on:
      - backend

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=goblin_assistant
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
EOF

# Create .env.example
cat > .env.example << 'EOF'
# Backend
DATABASE_URL=postgresql://postgres:postgres@db:5432/goblin_assistant
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here

# Frontend
VITE_API_URL=http://localhost:8001
EOF

# Create setup script
cat > scripts/setup.sh << 'EOF'
#!/bin/bash
set -e

echo "🔧 Setting up Goblin Assistant development environment..."

# Check if repos are cloned
if [ ! -d "../goblin-assistant-backend" ]; then
    echo "Cloning backend repository..."
    git clone git@github.com:fuaadabdullah/goblin-assistant-backend.git ../goblin-assistant-backend
fi

if [ ! -d "../goblin-assistant-frontend" ]; then
    echo "Cloning frontend repository..."
    git clone git@github.com:fuaadabdullah/goblin-assistant-frontend.git ../goblin-assistant-frontend
fi

# Copy environment file
if [ ! -f ../.env ]; then
    cp .env.example ../.env
    echo "⚠️  Created .env file. Please update with your credentials."
fi

# Install frontend dependencies
cd ../goblin-assistant-frontend
npm install

cd ../goblin-assistant-dev

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Update ../.env with your API keys"
echo "  2. Run: docker-compose up"
EOF

chmod +x scripts/setup.sh

# Create README
cat > README.md << 'EOF'
# Goblin Assistant Local Development

Local development environment for Goblin Assistant using Docker Compose.

## Quick Start

```bash
# First-time setup
./scripts/setup.sh

# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Services

- **Backend**: http://localhost:8001
- **Frontend**: http://localhost:5173
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Development Workflow

1. Clone this repo
2. Run setup script
3. Update `.env` with API keys
4. Start services with `docker-compose up`
5. Make changes in backend/frontend repos
6. Changes auto-reload (hot reload enabled)

## Troubleshooting

### Backend won't start
```bash
docker-compose down -v
docker-compose up --build
```

### Frontend dependencies issue
```bash
cd ../goblin-assistant-frontend
rm -rf node_modules package-lock.json
npm install
```

### Database issues
```bash
docker-compose down -v
docker-compose up db
# Wait for DB to start, then:
docker-compose up
```
EOF

git add .
git commit -m "Initial dev orchestration repository"
git branch -M main
git remote add origin "git@github.com:$GITHUB_USER/goblin-assistant-dev.git"

echo -e "${GREEN}✅ Dev repository created${NC}"

# Step 6: Create Contracts Package
echo -e "${GREEN}Step 6: Creating contracts package...${NC}"
cd "$WORKSPACE_ROOT"
rm -rf goblin-contracts
mkdir -p goblin-contracts
cd goblin-contracts
git init

mkdir -p src

# Create package.json
cat > package.json << 'EOF'
{
  "name": "@goblin/contracts",
  "version": "1.0.0",
  "description": "Shared TypeScript/Python contracts for Goblin Assistant",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "files": [
    "dist",
    "src"
  ],
  "scripts": {
    "build": "tsc",
    "test": "echo \"No tests yet\"",
    "prepublishOnly": "npm run build"
  },
  "repository": {
    "type": "git",
    "url": "git+https://github.com/fuaadabdullah/goblin-contracts.git"
  },
  "keywords": ["goblin", "assistant", "types", "contracts"],
  "author": "Fuaad Abdullah",
  "license": "MIT",
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
EOF

# Create TypeScript config
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "declaration": true,
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
EOF

# Create basic type definitions
cat > src/api.ts << 'EOF'
// API Request/Response Types

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  model?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  model: string;
  tokens_used?: number;
}

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'down';
  version: string;
  timestamp: string;
}

// Add more shared types here
EOF

# Create Python type stubs
cat > src/api.py << 'EOF'
"""Python type stubs for API contracts."""
from typing import Literal, Optional
from pydantic import BaseModel
from datetime import datetime

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    model: str
    tokens_used: Optional[int] = None

class HealthCheck(BaseModel):
    status: Literal["healthy", "degraded", "down"]
    version: str
    timestamp: str
EOF

# Create README
cat > README.md << 'EOF'
# @goblin/contracts

Shared TypeScript and Python type definitions for Goblin Assistant.

## Installation

### TypeScript (Frontend)
```bash
npm install @goblin/contracts
```

### Python (Backend)
```bash
# Via git
pip install git+https://github.com/fuaadabdullah/goblin-contracts.git@v1.0.0

# Or add to requirements.txt
goblin-contracts @ git+https://github.com/fuaadabdullah/goblin-contracts.git@v1.0.0
```

## Usage

### TypeScript
```typescript
import { ChatRequest, ChatResponse } from '@goblin/contracts';

const request: ChatRequest = {
  message: "Hello",
  model: "gpt-4"
};
```

### Python
```python
from goblin_contracts.api import ChatRequest, ChatResponse

request = ChatRequest(message="Hello", model="gpt-4")
```

## Versioning

This package follows [Semantic Versioning](https://semver.org/).

- `v1.0.0` - Initial release
- Breaking changes increment major version
- New fields increment minor version
- Bug fixes increment patch version

## Development

```bash
# Build TypeScript
npm run build

# Test
npm test
```
EOF

git add .
git commit -m "Initial contracts package"
git branch -M main
git remote add origin "git@github.com:$GITHUB_USER/goblin-contracts.git"

echo -e "${GREEN}✅ Contracts package created${NC}"

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}🎉 Migration Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Repositories created in:"
echo "  - $WORKSPACE_ROOT/goblin-assistant-backend"
echo "  - $WORKSPACE_ROOT/goblin-assistant-frontend"
echo "  - $WORKSPACE_ROOT/goblin-assistant-infra"
echo "  - $WORKSPACE_ROOT/goblin-assistant-dev"
echo "  - $WORKSPACE_ROOT/goblin-contracts"
echo ""
echo "Next steps:"
echo "  1. cd to each repo and run: git push -u origin main"
echo "  2. Add GitHub Actions workflows (see docs/ci-cd-workflows/)"
echo "  3. Configure GitHub secrets"
echo "  4. Test local dev: cd goblin-assistant-dev && ./scripts/setup.sh"
echo ""
echo -e "${YELLOW}⚠️  Don't forget to:${NC}"
echo "  - Update import paths in backend/frontend"
echo "  - Install contracts package in both repos"
echo "  - Configure CI/CD secrets"
echo "  - Update deployment configs"
echo ""
