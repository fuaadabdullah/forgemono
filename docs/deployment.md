---
description: 'Production deployment guide for ForgeMonorepo applications'
---

# Production Deployment

This guide covers the production deployment process, checklists, and best practices for applications in the ForgeMonorepo.

## Deployment Overview

The monorepo supports multiple deployment strategies depending on the application type and requirements:

- **Container-based**: Docker containers deployed to Fly.io, Kubernetes, or cloud providers
- **Serverless/Edge**: Frontend applications deployed to Vercel, Cloudflare Workers for edge logic
- **Hybrid**: Combination of containerized backends with serverless frontends

## Pre-Deployment Checklist

### 1. Secrets Management

- [ ] Use a managed secrets store (Bitwarden, AWS Secrets Manager, HashiCorp Vault)
- [ ] Never commit secrets to version control
- [ ] Rotate API keys and credentials regularly
- [ ] Use environment-specific secret sets (dev/staging/prod)

### 2. Build Preparation

```bash
# Build frontend for production (example)
cd apps/goblin-assistant/app
pnpm build

# Run comprehensive test suite
pnpm test
pytest -q

# Static analysis and linting
ruff .
prettier --check "**/*.{md,ts,js,json,css,py}"
```

### 3. Database Migrations

```bash
# For SQLAlchemy/Alembic-based services
cd apps/goblin-assistant/backend
alembic upgrade head

# Verify migration state
alembic current
```

### 4. Background Services

- [ ] Ensure worker processes (Celery, etc.) are configured
- [ ] Verify Redis/message queue connectivity
- [ ] Test background job processing
- [ ] Configure monitoring for worker health

## Deployment Options

### Container-Based Deployment

1. **Build container image**

   ```bash
   docker build -t my-app:latest .
   ```

2. **Deploy to target platform**
   - **Fly.io**: `fly deploy`
   - **Kubernetes**: Apply manifests with `kubectl`
   - **Cloud provider**: Use their container services (ECS, Cloud Run, etc.)

### Serverless Deployment

1. **Frontend applications**

   ```bash
   # Vercel deployment
   vercel --prod

   # Or configure automatic deployments via GitHub integration
   ```

2. **Edge functions**

   ```bash
   # Cloudflare Workers
   cd infra/cloudflare
   wrangler deploy
   ```

## Post-Deployment Verification

### Health Checks

- [ ] Verify `/health` endpoint returns healthy status
- [ ] Check `/v1/health/all` for comprehensive system health
- [ ] Test critical user flows end-to-end
- [ ] Validate API responses and data integrity

### Service Validation

- [ ] Confirm database connections and migrations
- [ ] Verify external API integrations
- [ ] Test authentication and authorization flows
- [ ] Validate file storage and CDN functionality

### Monitoring Setup

- [ ] Configure application monitoring (Sentry, etc.)
- [ ] Set up infrastructure monitoring (Prometheus, CloudWatch)
- [ ] Enable log aggregation and analysis
- [ ] Configure alerting for critical issues

## Security Checklist

### Network Security

- [ ] Implement rate limiting on public endpoints
- [ ] Configure Web Application Firewall (WAF) rules
- [ ] Set up proper CORS policies
- [ ] Use HTTPS with valid certificates

### Application Security

- [ ] Apply Content Security Policy (CSP) headers
- [ ] Implement proper input validation and sanitization
- [ ] Configure secure session management
- [ ] Enable security headers (HSTS, X-Frame-Options, etc.)

### Data Protection

- [ ] Encrypt sensitive data at rest
- [ ] Implement proper access controls (RBAC)
- [ ] Configure data backup and recovery procedures
- [ ] Set up data retention and deletion policies

## Rollback Procedures

### Quick Rollback

```bash
# Container rollback
kubectl rollout undo deployment/my-app

# Serverless rollback
vercel rollback
```

### Database Rollback

```bash
# Alembic rollback (if needed)
alembic downgrade -1

# Or restore from backup
# Follow your backup restoration procedures
```

## Monitoring & Observability

### Application Monitoring

- **Error Tracking**: Sentry for exception monitoring
- **Performance**: Application Performance Monitoring (APM)
- **User Analytics**: Track user interactions and conversion funnels

### Infrastructure Monitoring

- **System Metrics**: CPU, memory, disk usage
- **Service Health**: Response times, error rates, throughput
- **Log Aggregation**: Centralized logging with search capabilities

### Business Monitoring

- **Key Metrics**: User engagement, feature usage, conversion rates
- **SLA Monitoring**: Service Level Agreement compliance
- **Cost Monitoring**: Resource usage and cloud spending

## Troubleshooting

### Common Issues

- **Database Connection Issues**: Check connection strings and network ACLs
- **Service Unavailable**: Verify load balancer and auto-scaling configuration
- **Performance Degradation**: Check resource utilization and query optimization
- **Authentication Failures**: Validate token expiration and refresh mechanisms

### Debug Tools

```bash
# Check application logs
kubectl logs deployment/my-app

# Database connectivity test
psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# API endpoint testing
curl -H "Authorization: Bearer $TOKEN" https://api.example.com/health
```

### Emergency Contacts

- Development team Slack channel
- Infrastructure on-call rotation
- Cloud provider support contacts

## Infrastructure as Code

The `infra/` directory contains Terraform configurations and deployment scripts for:

- Cloud infrastructure provisioning
- Network configuration
- Security group setup
- Monitoring and alerting configuration

See `infra/README.md` for detailed infrastructure deployment instructions.

## Backup & Recovery

### Automated Backups

- Database snapshots scheduled via infrastructure automation
- File storage backups configured in cloud provider
- Configuration backups for critical systems

### Recovery Testing

- Regular disaster recovery drills
- Backup restoration validation
- Failover testing for high-availability setups

### Data Retention

- Implement data lifecycle policies
- Configure automated cleanup for old data
- Maintain compliance with data retention regulations

## Performance Optimization

### Application Performance

- Implement caching strategies (Redis, CDN)
- Optimize database queries and indexes
- Use connection pooling for database connections
- Implement lazy loading for frontend assets

### Infrastructure Scaling

- Configure auto-scaling based on metrics
- Implement load balancing across multiple instances
- Use read replicas for database scaling
- Consider CDN for static asset delivery

## Compliance & Audit

### Security Compliance

- Regular security assessments and penetration testing
- Compliance with industry standards (SOC 2, GDPR, etc.)
- Access logging and audit trails
- Regular dependency vulnerability scanning

### Operational Compliance

- Change management procedures
- Incident response and post-mortem processes
- Documentation of operational procedures
- Regular compliance audits and reporting
