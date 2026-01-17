# Production Deployment Checklist

## Pre-Deployment Verification

### 🔐 Security & Secrets
- [ ] All secrets moved to Bitwarden/vault (no hardcoded keys)
- [ ] `.env.production` created and populated with real values
- [ ] API keys rotated for production (separate from dev/staging)
- [ ] Database credentials validated (connection test passed)
- [ ] Redis connection tested and secured
- [ ] SSL/TLS certificates configured and valid

### 🗄️ Database & Data
- [ ] Database migrations tested in staging
- [ ] RLS (Row Level Security) policies validated: `bash scripts/ops/supabase_rls_check.sh`
- [ ] Backup strategy implemented and tested
- [ ] Data migration scripts prepared and tested
- [ ] Database connection pooling configured

### 📊 Monitoring & Observability
- [ ] Datadog agent configured with correct API key
- [ ] Sentry DSN configured and error tracking tested
- [ ] Redis monitoring enabled (memory, connections, latency)
- [ ] Application performance monitoring set up
- [ ] Log aggregation configured (Datadog/CloudWatch)

### 🚀 Application Configuration
- [ ] Environment variables validated
- [ ] Feature flags set for production
- [ ] Cache configuration tested (Redis connectivity)
- [ ] CDN/Edge configuration (Cloudflare) verified
- [ ] Rate limiting configured appropriately

### 🔄 CI/CD Pipeline
- [ ] GitHub Actions workflows updated for production
- [ ] Automated backup workflow scheduled and tested
- [ ] Deployment pipeline configured with proper environments
- [ ] Rollback procedures documented and tested

## Deployment Steps

### Phase 1: Infrastructure Setup
1. [ ] Provision production database (Supabase/AWS RDS)
2. [ ] Set up Redis instance (managed service)
3. [ ] Configure monitoring services (Datadog, Sentry)
4. [ ] Set up backup storage (S3/R2 with lifecycle policies)
5. [ ] Configure domain and SSL certificates

### Phase 2: Application Deployment
1. [ ] Deploy application to production environment
2. [ ] Run database migrations
3. [ ] Verify application health checks
4. [ ] Test critical user flows
5. [ ] Enable production monitoring

### Phase 3: Post-Deployment Validation
1. [ ] Monitor error rates and performance metrics
2. [ ] Verify backup creation and restoration
3. [ ] Test failover scenarios
4. [ ] Update documentation with production URLs
5. [ ] Notify stakeholders of successful deployment

## Rollback Plan

### Automated Rollback
- [ ] Previous deployment version identified
- [ ] Database backup created before deployment
- [ ] Rollback scripts tested in staging
- [ ] Monitoring alerts configured for rapid detection

### Manual Rollback Steps
1. [ ] Stop incoming traffic (maintenance mode)
2. [ ] Restore database from backup if needed
3. [ ] Rollback application to previous version
4. [ ] Verify system stability
5. [ ] Gradually restore traffic

## Monitoring & Alerts

### Critical Alerts (Page immediately)
- [ ] Application down/unreachable
- [ ] Database connection failures
- [ ] High error rates (>5%)
- [ ] Security incidents (failed auth, suspicious activity)

### Warning Alerts (Monitor closely)
- [ ] Increased latency (>500ms p95)
- [ ] High memory/CPU usage
- [ ] Backup failures
- [ ] Rate limit hits

### Info Alerts (Track trends)
- [ ] User growth metrics
- [ ] Performance degradation trends
- [ ] Feature usage statistics

## Performance Benchmarks

### Target Metrics
- [ ] API Response Time: <200ms p95
- [ ] Error Rate: <1%
- [ ] Uptime: >99.9%
- [ ] Cache Hit Rate: >80%
- [ ] Database Query Time: <50ms p95

### Scaling Thresholds
- [ ] CPU Usage: Alert at 70%, scale at 85%
- [ ] Memory Usage: Alert at 80%, scale at 90%
- [ ] Database Connections: Alert at 80% of limit
- [ ] Redis Memory: Alert at 80%, cleanup at 90%

## Security Checklist

### Infrastructure Security
- [ ] Network security groups/firewalls configured
- [ ] Database access restricted to application servers
- [ ] Redis access controlled via VPC/security groups
- [ ] API endpoints protected with authentication
- [ ] Secrets management implemented (Bitwarden/Vault)

### Application Security
- [ ] Input validation and sanitization implemented
- [ ] SQL injection prevention (use ORMs, prepared statements)
- [ ] XSS protection enabled
- [ ] CSRF protection configured
- [ ] Rate limiting implemented
- [ ] Security headers set (CSP, HSTS, etc.)

### Compliance & Audit
- [ ] Data retention policies defined
- [ ] Audit logging enabled
- [ ] GDPR/CCPA compliance reviewed
- [ ] Penetration testing completed
- [ ] Security monitoring active

## Disaster Recovery

### Recovery Time Objectives (RTO)
- [ ] Critical services: <1 hour
- [ ] Important services: <4 hours
- [ ] All other services: <24 hours

### Recovery Point Objectives (RPO)
- [ ] Critical data: <15 minutes data loss
- [ ] Important data: <1 hour data loss
- [ ] All other data: <24 hours data loss

### Recovery Procedures
1. [ ] Identify failure point and scope
2. [ ] Activate backup systems if needed
3. [ ] Restore from latest backup
4. [ ] Verify data integrity
5. [ ] Gradually restore services
6. [ ] Post-mortem analysis and improvements

## Communication Plan

### During Deployment
- [ ] Development team notified of deployment window
- [ ] Stakeholders informed of potential downtime
- [ ] Status page updated (if applicable)
- [ ] Communication channels monitored

### Post-Deployment
- [ ] Deployment results communicated to team
- [ ] Any issues and resolutions documented
- [ ] Performance metrics shared
- [ ] Lessons learned discussed

## Documentation Updates

### Post-Deployment Tasks
- [ ] Update runbooks with production procedures
- [ ] Document any custom configurations
- [ ] Update monitoring dashboards
- [ ] Create incident response playbooks
- [ ] Update team knowledge base

---

## Quick Commands Reference

```bash
# Environment setup
./scripts/setup-env-production.sh
./scripts/setup-production-db.sh
./scripts/setup-monitoring.sh

# Backup operations
./scripts/backup/pg_backup.sh

# Health checks
curl -f https://api.goblin.fuaad.ai/health
curl -f https://brain.goblin.fuaad.ai/health

# Monitoring
# Check Datadog: https://app.datadoghq.com/
# Check Sentry: https://sentry.io/
# Check Redis: redis-cli -u $REDIS_URL info

# Rollback (if needed)
# 1. Stop deployment
# 2. Restore from backup
# 3. Rollback application version
```

## Emergency Contacts

- **On-call Engineer**: [Phone/Slack handle]
- **Infrastructure Team**: [Contact info]
- **Security Team**: [Contact info]
- **Management**: [Contact info]

---

*Last Updated: December 30, 2025*
*Version: 1.0*
