# Forge Lite API - ECS Deployment Guide

This directory contains the complete ECS deployment configuration for the Forge Lite API backend.

## Overview

The deployment uses:

- **AWS ECS Fargate** for serverless container orchestration
- **Amazon ECR** for container registry
- **GitHub Actions** for CI/CD automation
- **CloudWatch** for logging and monitoring
- **Application Load Balancer** for traffic distribution

## Directory Structure

```
infra/deployments/ecs/
├── README.md                    # This file
├── task-definition.json         # ECS task definition
├── .github/workflows/           # GitHub Actions workflows
│   └── deploy-forge-lite-api.yml
└── scripts/
    └── setup-aws-infra.sh       # AWS infrastructure setup
```

## Prerequisites

1. **AWS Account** with appropriate permissions
1. **AWS CLI** installed and configured
1. **GitHub Repository** with secrets configured
1. **Docker** for local testing

### Required AWS Permissions

Your AWS user/role needs these permissions:

- `ecs:*`
- `ecr:*`
- `logs:*`
- `iam:*`
- `elasticloadbalancing:*`
- `ec2:*`

## Quick Start

### 1. Set Environment Variables

```bash
export AWS_REGION=us-east-1
export ENVIRONMENT=staging  # or production
```

### 2. Run Infrastructure Setup

```bash

# From the repository root
./tools/setup-aws-ecs.sh
```

This script will:

- Create ECR repository
- Set up VPC, subnets, and security groups
- Create ECS cluster
- Configure CloudWatch logging
- Register task definition
- Create ECS service

### 3. Configure GitHub Secrets

The setup script outputs required GitHub secrets. Add them to:
`<https://github.com/your-org/your-repo/settings/secrets/actions`>

Required secrets:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `ECR_REPOSITORY`

### 4. Deploy

Push to the main branch or trigger the workflow manually:

```bash
# Trigger deployment
gh workflow run deploy-forge-lite-api.yml -f environment=staging
```

## Configuration Files

### Task Definition (`task-definition.json`)

Defines the container configuration:

- **CPU/Memory**: 256 CPU units, 512 MB RAM
- **Port**: 8000 (FastAPI default)
- **Health Check**: `/health` endpoint
- **Environment Variables**: Configurable via task definition
- **Logging**: CloudWatch Logs

### GitHub Actions Workflow

**Triggers:**

- Push to `main` branch
- Manual workflow dispatch
- Pull requests (for validation)

**Stages:**

1. **Build**: Docker image build and ECR push
1. **Deploy**: ECS service update with new image
1. **Verify**: Health check and smoke tests

## Environment Management

### Staging Environment

```bash

ENVIRONMENT=staging ./tools/setup-aws-ecs.sh
```

- Cluster: `forge-lite-staging`
- Service: `forge-lite-api-staging`
- Separate VPC and resources

### Production Environment

```bash
ENVIRONMENT=production ./tools/setup-aws-ecs.sh
```

- Cluster: `forge-lite-production`
- Service: `forge-lite-api-production`
- Separate VPC and resources

## Monitoring and Troubleshooting

### Check Service Status

```bash

./tools/test-ecs-deployment.sh status
```

### View Logs

```bash
# Last 50 lines
./tools/test-ecs-deployment.sh logs

# Last 100 lines
./tools/test-ecs-deployment.sh logs 100

# Follow logs
aws logs tail /ecs/forge-lite-api --region us-east-1 --follow
```

### Test API Health

```bash

./tools/test-ecs-deployment.sh health
```

### Force Deployment

```bash
./tools/test-ecs-deployment.sh deploy
```

### Scale Service

```bash

# Scale to 2 tasks
./tools/test-ecs-deployment.sh scale 2
```

## Load Balancer Setup (Optional)

For production deployments, add an Application Load Balancer:

1. Create ALB in AWS Console
1. Create target group (port 8000, health check path `/health`)
1. Update ECS service to use load balancer
1. Update security groups for ALB access

## Cost Optimization

### Fargate Pricing

- **CPU**: $0.04048 per vCPU-hour
- **Memory**: $0.004445 per GB-hour
- **Data Transfer**: $0.09 per GB

### Cost Saving Tips

- Use smaller instance sizes for dev/staging
- Scale to zero when not in use (requires custom setup)
- Use Spot Instances for non-critical workloads
- Monitor with AWS Cost Explorer

## Security Considerations

### Network Security

- Tasks run in private subnets
- Security groups restrict access to port 8000
- Use VPC endpoints for AWS services

### Container Security

- Non-root user execution
- Minimal base image (python:3.11-slim)
- Regular security scanning with ECR

### Secrets Management

- Use AWS Secrets Manager or Parameter Store
- Never store secrets in environment variables
- Rotate credentials regularly

## Troubleshooting Common Issues

### Service Won't Start

```bash
# Check task definition
aws ecs describe-task-definition --task-definition forge-lite-api-staging

# Check service events
aws ecs describe-services --cluster forge-lite-staging --services forge-lite-api-staging --query 'services[0].events'
```

### Health Check Failures
```bash

# Check container logs
aws logs tail /ecs/forge-lite-api --region us-east-1

# Verify health endpoint locally
curl <http://localhost:8000/health>
```

### Deployment Failures

```bash
# Check GitHub Actions logs
# Look for ECR push or ECS update failures

# Manual deployment
aws ecs update-service --cluster forge-lite-staging --service forge-lite-api-staging --force-new-deployment
```

## Cleanup

To remove all resources:

```bash

# Delete service
aws ecs delete-service --cluster forge-lite-staging --service forge-lite-api-staging --force

# Delete cluster
aws ecs delete-cluster --cluster forge-lite-staging

# Delete ECR repository
aws ecr delete-repository --repository-name forge-lite-api --force

# Delete VPC resources (if created by script)

# Note: Manual cleanup required for VPC, subnets, security groups
```

## Support

For issues:

1. Check AWS service health dashboard
1. Review CloudWatch logs
1. Check GitHub Actions workflow runs
1. Consult AWS ECS documentation

## Related Documentation

- [AWS ECS User Guide](https://docs.aws.amazon.com/ecs/)
- [GitHub Actions for AWS](https://github.com/aws-actions)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Forge Lite API README](../../apps/forge-lite/api/README.md)
