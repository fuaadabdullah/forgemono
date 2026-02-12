# GoblinOS Backend Integration

This directory contains integration points with the GoblinOS automation system.

## Overview

GoblinOS is the central automation and orchestration system for the ForgeMonorepo. The Goblin Assistant integrates with GoblinOS for:

- Task orchestration and execution
- Guild-based role management
- Automated deployment and monitoring
- Cross-service communication

## Integration Points

- **API Endpoints**: The FastAPI backend in `../backend/` integrates with GoblinOS services
- **Configuration**: Shared configuration in `../config/` includes GoblinOS settings
- **Monitoring**: Datadog monitoring in `../datadog/` covers GoblinOS operations
- **Infrastructure**: Infrastructure as code in `../infra/` deploys GoblinOS components

## Key Components

- **Goblin CLI**: Command-line interface for GoblinOS operations
- **Guild System**: Role-based access and automation
- **Task Orchestration**: Multi-step task execution with dependencies
- **Monitoring & Alerting**: Integrated observability stack

## Development

For GoblinOS development and integration:

1. Refer to the main GoblinOS documentation at `../../../GoblinOS/README.md`
2. Use the Goblin CLI: `../../../GoblinOS/goblin-cli.sh`
3. Check guild configurations: `../../../GoblinOS/goblins.yaml`

## Deployment

GoblinOS components are deployed via the infrastructure configurations in `../infra/` and orchestrated through the deployment pipelines.
