---
description: 'ForgeMonorepo project structure and organization'
---

# Project Structure

The ForgeMonorepo is organized as a unified workspace containing multiple applications, tools, and supporting infrastructure. This document provides a comprehensive overview of the codebase organization and key directories.

## Repository Overview

```text
ForgeMonorepo/
├── apps/                    # Active applications and projects
├── GoblinOS/               # Primary platform (pnpm workspace)
├── infra/                  # Infrastructure as code
├── tools/                  # Utility scripts and automation
├── docs/                   # Documentation
├── portfolio/              # Personal assets and demos
├── artifacts/              # Generated outputs
└── shared/                 # Cross-project shared code
```

## Core Directories

### `apps/` - Applications

Contains all active applications and projects, organized by technology and purpose:

```text
apps/
├── goblin-assistant/       # Main AI assistant application
│   ├── backend/           # FastAPI backend
│   ├── app/              # Next.js frontend
│   ├── docs/             # App-specific documentation
│   └── tests/            # Application tests
├── gaslight/             # Additional applications
├── forge-lite/           # Trading/finance applications
└── python/               # Python-based tools
```

**Key Applications:**

- **goblin-assistant**: Primary AI assistant with web interface, API backend, and AI integrations
- **gaslight**: Authentication and user management services
- **forge-lite**: Financial/trading applications
- **python**: Standalone Python utilities and tools

### `GoblinOS/` - Core Platform

The primary platform built as a pnpm workspace:

```text
GoblinOS/
├── packages/              # Core packages
│   ├── core/             # Core functionality
│   ├── cli/              # Command-line interface
│   ├── plugins/          # Extensible plugins
│   └── shared/           # Shared utilities
├── docs/                 # Platform documentation
├── scripts/              # Build and development scripts
└── config/               # Platform configuration
```

**Components:**

- **packages/core**: Core business logic and AI orchestration
- **packages/cli**: Command-line tools for development and deployment
- **packages/plugins**: Extensible plugin system for custom functionality
- **packages/shared**: Common utilities and helpers

### `infra/` - Infrastructure

Infrastructure as code and deployment configurations:

```text
infra/
├── terraform/            # Terraform configurations
├── docker/              # Docker configurations
├── kubernetes/          # K8s manifests
├── cloudflare/          # Edge deployment configs
└── scripts/             # Infrastructure scripts
```

**Infrastructure Components:**

- **terraform**: Cloud infrastructure provisioning
- **docker**: Container definitions and compose files
- **kubernetes**: Container orchestration manifests
- **cloudflare**: Edge computing and CDN configuration

### `tools/` - Utilities and Automation

Utility scripts and automation tools:

```text
tools/
├── scripts/             # Bash/Python automation scripts
├── docker/              # Docker-related utilities
├── ci/                  # CI/CD helper scripts
└── development/         # Development environment tools
```

**Tool Categories:**

- **scripts**: General-purpose automation and maintenance scripts
- **docker**: Container management and deployment utilities
- **ci**: Continuous integration and deployment helpers
- **development**: Local development environment setup

### `docs/` - Documentation

Comprehensive documentation system:

```text
docs/
├── README.md            # Documentation index
├── getting-started.md   # Setup and development guide
├── deployment.md        # Production deployment guide
├── architecture/        # System architecture docs
├── api/                 # API documentation
├── guides/              # User and developer guides
└── templates/           # Document templates
```

**Documentation Areas:**

- **getting-started.md**: Development environment setup
- **deployment.md**: Production deployment procedures
- **architecture**: System design and architecture documentation
- **api**: API reference and integration guides
- **guides**: Tutorials and how-to documentation

## Supporting Directories

### `portfolio/` - Personal Assets

Personal branding and project assets:

```text
portfolio/
├── resume/              # Resume and CV materials
├── projects/            # Project write-ups and demos
└── assets/              # Images, presentations, etc.
```

### `artifacts/` - Generated Outputs

Build artifacts and generated content:

```text
artifacts/
├── builds/              # Build outputs
├── reports/             # Generated reports
├── diagrams/            # Auto-generated diagrams
└── exports/             # Data exports
```

### `shared/` - Cross-Project Code

Shared code and utilities used across multiple applications:

```text
shared/
├── components/          # Reusable UI components
├── libraries/           # Shared libraries
├── configs/             # Common configurations
└── types/               # TypeScript type definitions
```

## Configuration Files

### Root Level Configuration

- `package.json` & `pnpm-workspace.yaml`: Node.js workspace configuration
- `pyproject.toml`: Python project configuration
- `docker-compose.yml`: Local development services
- `.github/`: GitHub Actions and configuration
- `infra/`: Infrastructure as code configurations

### Application Configuration

Each application in `apps/` contains its own configuration:

- `requirements.txt` / `pyproject.toml`: Python dependencies
- `package.json`: Node.js dependencies
- `.env.example`: Environment variable templates
- Application-specific configuration files

## Development Workflow

### Local Development

1. **Setup**: Follow `docs/getting-started.md`
2. **Application Development**: Work in respective `apps/` directories
3. **Shared Development**: Modify `shared/` for cross-project changes
4. **Infrastructure Changes**: Update `infra/` for deployment modifications

### Testing Strategy

- **Unit Tests**: Located in each application's `tests/` or `__tests__/` directory
- **Integration Tests**: In `tools/ci/` for cross-application testing
- **End-to-End Tests**: Application-specific E2E test suites

### Build and Deployment

- **Build Scripts**: Located in application directories and `tools/scripts/`
- **CI/CD**: GitHub Actions in `.github/workflows/`
- **Deployment**: Infrastructure configurations in `infra/`
- **Release**: Version management and release scripts in `tools/`

## Code Organization Principles

### Separation of Concerns

- **Applications**: Self-contained in `apps/` with their own dependencies and configurations
- **Platform**: Core platform logic isolated in `GoblinOS/`
- **Infrastructure**: Deployment and infrastructure concerns separated in `infra/`
- **Tools**: Automation and utilities centralized in `tools/`

### Shared Resources

- **Common Code**: Placed in `shared/` when used across multiple applications
- **Documentation**: Centralized in `docs/` with application-specific docs in `apps/*/docs/`
- **Configuration**: Application-specific configs in app directories, shared configs in `shared/configs/`

### Naming Conventions

- **Directories**: kebab-case (e.g., `goblin-assistant`, `shared-components`)
- **Files**: kebab-case for documentation, camelCase for code files
- **Applications**: Prefixed with purpose (e.g., `goblin-` for AI assistant related)

## Contributing

### Adding New Applications

1. Create new directory in `apps/`
2. Add application-specific configuration files
3. Update workspace configurations if needed
4. Add documentation in `apps/{name}/README.md`
5. Update root `README.md` project map

### Modifying Shared Code

1. Update `shared/` directories
2. Test changes across all affected applications
3. Update documentation if APIs change
4. Ensure backward compatibility

### Infrastructure Changes

1. Update `infra/` configurations
2. Test deployments in staging environment
3. Update deployment documentation
4. Coordinate with team for production deployment

## Maintenance

### Regular Tasks

- **Dependency Updates**: Use automation scripts in `tools/scripts/`
- **Security Audits**: Run security scanning tools
- **Documentation Updates**: Keep docs synchronized with code changes
- **Cleanup**: Remove deprecated code and unused artifacts

### Monitoring and Metrics

- **Build Health**: CI/CD pipeline status monitoring
- **Code Quality**: Automated linting and testing results
- **Documentation Coverage**: Documentation completeness metrics
- **Performance**: Application performance monitoring

## Troubleshooting

### Common Issues

- **Import Errors**: Check workspace configuration and dependency installation
- **Build Failures**: Verify all required tools and dependencies are installed
- **Test Failures**: Check test configuration and environment setup
- **Deployment Issues**: Validate infrastructure configurations and permissions

### Getting Help

- Check application-specific READMEs in `apps/*/README.md`
- Review documentation in `docs/`
- Check existing issues and pull requests
- Contact the development team through appropriate channels
