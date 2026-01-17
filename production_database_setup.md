# Production Database Setup for Goblin Assistant

- [x] Analyze current database configuration
- [x] Research available database options
- [ ] Set up production database instance
- [ ] Configure database connection and authentication
- [ ] Update environment variables
- [ ] Run database migrations
- [ ] Test database connectivity
- [ ] Configure backup and monitoring

## Current Database Analysis

### Existing Configuration
- **Current Setup**: Development SQLite database (`sqlite:///./goblin_assistant.db`)
- **Database URL**: Configured in environment variables
- **Current Location**: Local SQLite file in project root
- **Backend**: FastAPI with SQLAlchemy async support
- **ORM**: SQLAlchemy with asyncpg driver for PostgreSQL

### Database Requirements
Based on the code analysis, the application needs:
- PostgreSQL database for production
- Async connection support
- Connection pooling
- SSL/TLS encryption
- Row-level security
- Backup and monitoring capabilities

## Recommended Production Database Options

### Option 1: Supabase (Recommended)
**Pros:**
- Built-in PostgreSQL with managed hosting
- Automatic backups and monitoring
- Built-in authentication and authorization
- Real-time subscriptions
- Edge functions support
- Easy integration with existing Supabase setup

**Cons:**
- Vendor lock-in
- Limited customization options

**Setup Steps:**
1. Create Supabase project (already exists)
2. Configure production database
3. Set up row-level security
4. Configure backup policies
5. Update environment variables

### Option 2: AWS RDS PostgreSQL
**Pros:**
- Full control over database
- High availability and automatic backups
- Scalable infrastructure
- Enterprise-grade security
- Multi-region deployment

**Cons:**
- Higher cost
- More complex setup
- Requires AWS expertise

**Setup Steps:**
1. Create RDS PostgreSQL instance
2. Configure security groups
3. Set up automated backups
4. Configure connection pooling
5. Update environment variables

### Option 3: Railway PostgreSQL
**Pros:**
- Simple deployment
- Built-in connection pooling
- Automatic SSL certificates
- Preview environments
- Easy CI/CD integration

**Cons:**
- Newer service with less track record
- Limited enterprise features

**Setup Steps:**
1. Create Railway project
2. Add PostgreSQL service
3. Configure environment variables
4. Set up connection pooling
5. Configure backups

### Option 4: Google Cloud SQL PostgreSQL
**Pros:**
- Google Cloud integration
- High availability options
- Automatic backups
- Enterprise security
- Global deployment

**Cons:**
- Google Cloud ecosystem dependency
- Complex pricing model

**Setup Steps:**
1. Create Cloud SQL instance
2. Configure private networking
3. Set up IAM authentication
4. Configure backup policies
5. Update environment variables

## Implementation Plan

### Phase 1: Database Setup
1. Choose database provider (recommend Supabase for simplicity)
2. Create production database instance
3. Configure security settings
4. Set up connection pooling
5. Configure SSL/TLS

### Phase 2: Application Configuration
1. Update environment variables
2. Configure database migrations
3. Set up connection pooling
4. Configure monitoring
5. Test connectivity

### Phase 3: Security & Backup
1. Enable row-level security
2. Configure backup policies
3. Set up monitoring alerts
4. Configure log rotation
5. Test disaster recovery

### Phase 4: Production Deployment
1. Deploy application with new database
2. Run database migrations
3. Verify all functionality
4. Monitor performance
5. Document procedures

## Environment Variables

### Production Database Configuration
```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database?sslmode=require
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=0
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30

# Monitoring Configuration
DATABASE_MONITORING=true
SLOW_QUERY_THRESHOLD=1000
CONNECTION_TIMEOUT=10
```

### Security Configuration
```bash
# SSL/TLS Configuration
DATABASE_SSL_MODE=require
DATABASE_SSL_CERT=/path/to/certificate.pem
DATABASE_SSL_KEY=/path/to/private-key.pem
DATABASE_SSL_CA=/path/to/ca-certificate.pem

# Row-Level Security
ROW_LEVEL_SECURITY=true
RLS_ENABLED_TABLES=conversations,messages,users

# Access Control
DATABASE_USER_ROLE=app_user
DATABASE_READONLY_USER=app_readonly
```

## Next Steps

1. **Choose Database Provider**: Supabase (recommended) or AWS RDS
2. **Create Database Instance**: Set up production database
3. **Configure Security**: Set up SSL, RLS, and access controls
4. **Update Configuration**: Modify environment variables
5. **Test Connection**: Verify database connectivity
6. **Run Migrations**: Deploy schema changes
7. **Configure Monitoring**: Set up performance monitoring
8. **Test Application**: Verify all functionality works

## Estimated Timeline
- Database setup: 2-4 hours
- Application configuration: 1-2 hours
- Security configuration: 1-2 hours
- Testing and validation: 1-2 hours
- **Total**: 5-10 hours