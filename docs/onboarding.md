---
description: "Complete onboarding guide for new developers joining the ForgeMonorepo project"
---

# Onboarding Guide

Welcome to the ForgeMonorepo! This guide will help you get up and running as a new developer on the project.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js 18+** and **pnpm**
- **Python 3.9+** with pip
- **Docker** and **Docker Compose**
- **Git** for version control
- **VS Code** with recommended extensions

## Initial Setup

### 1. Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/your-org/ForgeMonorepo.git
cd ForgeMonorepo

# Install Node.js dependencies
pnpm install

# Setup Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment templates
cp .env.example .env.local

# Setup local development services
docker-compose up -d
```

### 3. Verify Setup

```bash
# Test Node.js applications
pnpm test

# Test Python applications
python -m pytest

# Check documentation quality
python tools/doc-quality/doc_quality_check.py
```

## Understanding the Architecture

### Core Concepts

- **Monorepo Structure**: Multiple applications and tools in a single repository
- **GoblinOS Platform**: Primary AI orchestration platform built with pnpm workspaces
- **Modular Applications**: Independent applications in `apps/` directory
- **Shared Infrastructure**: Common services and utilities in `shared/`

### Key Applications

1. **goblin-assistant**: Main AI assistant application
   - Frontend: Next.js web interface
   - Backend: FastAPI with AI integrations
   - Features: Chat interface, model routing, telemetry

2. **gaslight**: Authentication and user management
   - User registration and login
   - Session management
   - Security features

3. **forge-lite**: Financial/trading applications
   - Market data integration
   - Trading interfaces
   - Risk management tools

## Development Workflow

### Daily Development

1. **Pull latest changes**: `git pull origin main`
2. **Create feature branch**: `git checkout -b feature/your-feature`
3. **Make changes** following the established patterns
4. **Run tests**: `pnpm test` and `python -m pytest`
5. **Check documentation**: `python tools/doc-quality/doc_quality_check.py`
6. **Commit changes**: `git commit -m "feat: add your feature"`
7. **Push and create PR**: `git push origin feature/your-feature`

### Code Quality Standards

- **TypeScript/ESLint**: Must pass without errors
- **Python linting**: Follow PEP 8 and project standards
- **Testing**: Unit tests required for new features
- **Documentation**: Update docs for API changes
- **Security**: No secrets committed, use environment variables

## Key Resources

### Documentation

- **[Getting Started](getting-started.md)**: Development environment setup
- **[Project Structure](project-structure.md)**: Repository organization
- **[Deployment](deployment.md)**: Production deployment procedures
- **[Documentation System](documentation-system.md)**: AI analysis and quality tools

### Important Files

- `README.md`: Project overview and navigation
- `package.json`: Node.js workspace configuration
- `pyproject.toml`: Python project configuration
- `docker-compose.yml`: Local development services
- `.github/workflows/`: CI/CD pipelines

### Communication

- **Issues**: GitHub Issues for bugs and features
- **Discussions**: GitHub Discussions for questions
- **Pull Requests**: Code review process
- **Documentation**: Wiki and docs/ directory

## Getting Help

### First Steps

1. **Read the documentation**: Start with this guide and the getting started docs
2. **Explore the codebase**: Look at existing applications in `apps/`
3. **Run the applications**: Follow the getting started guide
4. **Ask questions**: Use GitHub Discussions for help

### Common Issues

- **Environment setup**: Check the getting started guide
- **Dependencies**: Run `pnpm install` and check Python requirements
- **Docker issues**: Ensure Docker Desktop is running
- **Permission errors**: Check file permissions and environment variables

### Support Channels

- **Documentation**: Check docs/ directory first
- **GitHub Issues**: For bugs and technical problems
- **Team chat**: For quick questions and collaboration
- **Code reviews**: Learn from PR feedback

## Next Steps

After completing this onboarding:

1. **Set up your development environment** completely
2. **Run all applications** and understand their functionality
3. **Read the architecture documentation** in `docs/architecture/`
4. **Pick a small task** from GitHub Issues to get started
5. **Familiarize yourself** with the CI/CD pipelines

Welcome to the team! 🎉
