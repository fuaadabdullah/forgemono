---
description: 'Getting started with ForgeMonorepo development'
---

# Getting Started

This guide covers the initial setup and development workflow for the ForgeMonorepo.

## Prerequisites

- **Node.js**: Version 20 or 22 with pnpm package manager
- **Python**: Version 3.11 or higher with pip
- **Docker Desktop**: For containerized services (optional but recommended)
- **Git**: For version control

## Quick Start

Get up and running with the basic development environment:

```bash
# Clone the repository
git clone https://github.com/fuaadabdullah/forgemono.git
cd ForgeMonorepo

# Install Node.js workspace packages
pnpm install

# GoblinOS development
cd GoblinOS
pnpm install
pnpm build
pnpm test
```

For AI features and advanced commands, see `GoblinOS/README.md`.

## Development Environment Setup

### 1. Repository Setup

```bash
git clone https://github.com/fuaadabdullah/forgemono.git
cd ForgeMonorepo
```

### 2. Node.js Dependencies

Install workspace packages for JavaScript tools and frontend applications:

```bash
pnpm install
```

### 3. Python Environment

Create a virtual environment and install Python dependencies:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Goblin Assistant backend dependencies (example)
pip install -r apps/goblin-assistant/requirements.txt
pip install -r apps/goblin-assistant/api/requirements.txt
```

### 4. Environment Variables

Configure environment variables for the applications you're working on:

```bash
# Copy environment template (example for Goblin Assistant)
cp apps/goblin-assistant/backend/.env.example apps/goblin-assistant/backend/.env.local

# Edit with your values (database connections, API keys, etc.)
# See apps/goblin-assistant/README.md for detailed configuration
```

For secrets management, consider using Bitwarden as described in the application-specific READMEs.

### 5. Backend Development (FastAPI)

Start the backend server for development:

```bash
cd apps/goblin-assistant

# Start with auto-reload
uvicorn backend.main:app --reload --port 8001

# Or use project-specific startup scripts if available
```

### 6. Frontend Development

If working on frontend applications:

```bash
cd apps/goblin-assistant/app

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

## Testing & Quality Assurance

### Running Tests

```bash
# Python tests
pytest -q

# JavaScript/TypeScript tests (where applicable)
pnpm test
```

### Code Quality Checks

```bash
# Python linting and formatting
ruff .

# JavaScript/TypeScript formatting
prettier --check "**/*.{md,ts,js,json,css,py}"
```

## Development Notes

- **Application-Specific Setup**: Many applications have their own detailed READMEs. Always check `apps/{app-name}/README.md` for app-specific instructions.

- **Docker Services**: For production-like local development, use Docker for services like PostgreSQL and Redis. See the `docker/` and `infra/` directories.

- **Hot Reloading**: Backend services typically support hot reloading during development for faster iteration.

- **Environment Isolation**: Use virtual environments for Python and consider using tools like `direnv` for automatic environment activation.

## Next Steps

- Read the [project structure documentation](./project-structure.md) to understand the codebase organization
- Follow the [onboarding guide](./onboarding.md) for contribution guidelines
- Check [deployment documentation](./deployment.md) when ready to deploy changes
