# Pull Request Checklist

This checklist ensures that pull requests meet quality, security, and architectural standards before merging.

## Code Quality

- [ ] **Linting & Formatting**: All linting passes (Black, Ruff, ESLint, etc.)
- [ ] **Type Checking**: TypeScript and Python type checking passes
- [ ] **Tests**: Unit tests pass locally and in CI
- [ ] **Coverage**: Test coverage meets minimum thresholds

## Security & Compliance

- [ ] **Secrets**: No secrets committed; all sensitive data uses environment variables or Vault
- [ ] **Dependencies**: No vulnerable dependencies (npm audit, safety check)
- [ ] **RBAC**: Database Row Level Security policies included for new tables
- [ ] **API Keys**: Provider keys are properly masked and rotated

## Architecture & Design

- [ ] **Background Tasks**: No duplicate background tasks created (CI check passes)
- [ ] **Database**: Migrations included and tested for schema changes
- [ ] **API Contracts**: TypeScript/Python contracts stay synchronized
- [ ] **Performance**: No N+1 queries or inefficient operations added

## Documentation

- [ ] **Code Comments**: Complex logic is documented
- [ ] **README Updates**: Feature changes documented in relevant READMEs
- [ ] **API Documentation**: New endpoints documented with examples
- [ ] **Migration Notes**: Breaking changes documented for deployment

## Testing & Validation

- [ ] **Integration Tests**: Cross-service interactions tested
- [ ] **E2E Tests**: Critical user flows tested
- [ ] **Load Testing**: Performance impact assessed for high-traffic features
- [ ] **Accessibility**: UI changes meet WCAG standards

## Deployment Readiness

- [ ] **Environment Variables**: All required env vars documented
- [ ] **Feature Flags**: New features behind feature flags if needed
- [ ] **Rollback Plan**: Clear rollback strategy for complex changes
- [ ] **Monitoring**: Appropriate metrics and alerts added

## Review Requirements

- [ ] **Self-Review**: PR creator has reviewed their own changes
- [ ] **Peer Review**: At least one team member has reviewed
- [ ] **Domain Expert**: Complex changes reviewed by relevant domain expert
- [ ] **Security Review**: Security-sensitive changes reviewed by security team

## CI/CD Validation

- [ ] **CI Pipeline**: All CI checks pass (lint, test, build, security)
- [ ] **Preview Deployments**: Frontend changes tested in preview environments
- [ ] **Staging Tests**: Integration tests pass in staging
- [ ] **Production Readiness**: Release checklist completed for production changes

---

**Note**: This checklist is enforced by automated CI checks where possible. Manual review is required for items marked with ⚠️.

**Last Updated**: December 2025</content>
<parameter name="filePath">/Users/fuaadabdullah/ForgeMonorepo/docs/PR_CHECKLIST.md
