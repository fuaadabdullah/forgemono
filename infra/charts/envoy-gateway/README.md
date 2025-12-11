---title: Envoy Gateway for Overmind
type: reference
project: GoblinOS/Overmind
status: published
owner: GoblinOS
goblin_name: Overmind Envoy Gateway
description: "README"

---

# Envoy Gateway Ingress

Advanced ingress for Overmind using [Envoy Gateway](https://gateway.envoyproxy.io/).

## Overview

Envoy Gateway provides:

- ✅ **Advanced routing** - Path-based, header-based, query parameter routing
- ✅ **mTLS** - Mutual TLS between gateway and backend services
- ✅ **Rate limiting** - Per-route, per-user, global rate limits
- ✅ **Authentication** - JWT, OIDC, external auth
- ✅ **Request transformation** - Header manipulation, body modification
- ✅ **Circuit breaking** - Prevent cascading failures
- ✅ **Observability** - Access logs, metrics, distributed tracing

## Architecture

```
Internet
    │
    ▼
┌─────────────────────────────────────────┐
│       Envoy Gateway (Gateway API)       │
│  - TLS Termination                      │
│  - Rate Limiting (10/100/500 req/sec)   │
│  - CORS, Security Headers               │
│  - Request/Response Transformation      │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┴─────────┬─────────────┐
    ▼                   ▼             ▼
┌─────────┐      ┌──────────┐   ┌──────────┐
│Dashboard│      │   API    │   │  Bridge  │
│  :80    │      │  :8000   │   │  :3030   │
└─────────┘      └──────────┘   └──────────┘

Hostnames:

- dashboard.overmind.example.com → Dashboard
- api.overmind.example.com → API
- api.overmind.example.com/bridge → Bridge
```

## Quick Start

### Install Envoy Gateway

```bash
# Install Gateway API CRDs
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml

# Install Envoy Gateway
helm install eg oci://docker.io/envoyproxy/gateway-helm \
  --version v1.0.0 \
  -n envoy-gateway-system \
  --create-namespace

# Verify installation
kubectl wait --timeout=5m -n envoy-gateway-system \
  deployment/envoy-gateway --for=condition=Available
```

### Deploy Gateway Resources

```bash

# Apply Gateway and HTTPRoutes
kubectl apply -f gateway/gateway.yaml
kubectl apply -f gateway/httproutes/

# Verify Gateway
kubectl get gateway -n overmind-prod
kubectl describe gateway overmind-gateway -n overmind-prod
```

### Get Gateway Address

```bash
# Get LoadBalancer IP/hostname
kubectl get gateway overmind-gateway -n overmind-prod \
  -o jsonpath='{.status.addresses[0].value}'

# Update DNS records
# dashboard.overmind.example.com → <gateway-address>
# api.overmind.example.com → <gateway-address>
```

### Test Routing

```bash

# Test dashboard route
curl -H "Host: dashboard.overmind.example.com" <http://<gateway-address>/>

# Test API route
curl -H "Host: api.overmind.example.com" <http://<gateway-address>/health>

# Test bridge route
curl -H "Host: api.overmind.example.com" <http://<gateway-address>/bridge/health>
```

## Gateway Configuration

### Gateway Resource

**File:** `gateway/gateway.yaml`

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: overmind-gateway
  namespace: overmind-prod
spec:
  gatewayClassName: eg
  listeners:
  # HTTP (redirect to HTTPS)
  - name: http
    protocol: HTTP
    port: 80
    hostname: "*.overmind.example.com"

  # HTTPS
  - name: https
    protocol: HTTPS
    port: 443
    hostname: "*.overmind.example.com"
    tls:
      mode: Terminate
      certificateRefs:
      - name: overmind-tls
        kind: Secret
```

### HTTPRoute - Dashboard

**File:** `gateway/httproutes/dashboard.yaml`

```yaml

apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: dashboard
  namespace: overmind-prod
spec:
  parentRefs:

  - name: overmind-gateway
    sectionName: https

  hostnames:

  - dashboard.overmind.example.com

  rules:

  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:

    - name: overmind-dashboard
      port: 80
```

### HTTPRoute - API with Rate Limiting

**File:** `gateway/httproutes/api.yaml`

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api
  namespace: overmind-prod
spec:
  parentRefs:
  - name: overmind-gateway
    sectionName: https

  hostnames:
  - api.overmind.example.com

  rules:
  # API endpoints (with auth)
  - matches:
    - path:
        type: PathPrefix
        value: /api
      headers:
      - name: Authorization
        value: .+
        type: RegularExpression
    filters:
    - type: ExtensionRef
      extensionRef:
        group: gateway.envoyproxy.io
        kind: RateLimitPolicy
        name: authenticated-rate-limit
    backendRefs:
    - name: overmind-api
      port: 8000

  # Public endpoints (no auth, stricter limits)
  - matches:
    - path:
        type: PathPrefix
        value: /api
    filters:
    - type: ExtensionRef
      extensionRef:
        group: gateway.envoyproxy.io
        kind: RateLimitPolicy
        name: anonymous-rate-limit
    backendRefs:
    - name: overmind-api
      port: 8000
```

## Rate Limiting

### RateLimitPolicy - Anonymous

**File:** `gateway/rate-limits/anonymous.yaml`

```yaml

apiVersion: gateway.envoyproxy.io/v1alpha1
kind: RateLimitPolicy
metadata:
  name: anonymous-rate-limit
  namespace: overmind-prod
spec:
  rateLimits:

  - clientSelectors:
    - headers:
      - name: X-Forwarded-For
        type: Distinct
    limits:
      requests: 10
      unit: Second
```

### RateLimitPolicy - Authenticated

**File:** `gateway/rate-limits/authenticated.yaml`

```yaml
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: RateLimitPolicy
metadata:
  name: authenticated-rate-limit
  namespace: overmind-prod
spec:
  rateLimits:
  - clientSelectors:
    - headers:
      - name: Authorization
        type: Distinct
    limits:
      requests: 100
      unit: Second
```

### RateLimitPolicy - Global

**File:** `gateway/rate-limits/global.yaml`

```yaml

apiVersion: gateway.envoyproxy.io/v1alpha1
kind: RateLimitPolicy
metadata:
  name: global-rate-limit
  namespace: overmind-prod
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: Gateway
    name: overmind-gateway

  rateLimits:

  - limits:
      requests: 1000
      unit: Second
```

## Backend TLS (mTLS)

### BackendTLSPolicy

**File:** `gateway/backend-tls/api.yaml`

```yaml
apiVersion: gateway.networking.k8s.io/v1alpha2
kind: BackendTLSPolicy
metadata:
  name: api-backend-tls
  namespace: overmind-prod
spec:
  targetRef:
    group: ""
    kind: Service
    name: overmind-api

  tls:
    hostname: overmind-api.overmind-prod.svc.cluster.local
    caCertRefs:
    - name: overmind-ca
      kind: ConfigMap
```

## CORS Configuration

### SecurityPolicy - CORS

**File:** `gateway/security/cors.yaml`

```yaml

apiVersion: gateway.envoyproxy.io/v1alpha1
kind: SecurityPolicy
metadata:
  name: cors-policy
  namespace: overmind-prod
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: Gateway
    name: overmind-gateway

  cors:
    allowOrigins:

    - <https://dashboard.overmind.example.com>
    - <https://*.overmind.example.com>
    allowMethods:

    - GET
    - POST
    - PUT
    - DELETE
    - OPTIONS
    allowHeaders:

    - Content-Type
    - Authorization
    - X-Request-ID
    exposeHeaders:

    - X-Request-ID
    - X-RateLimit-Limit
    - X-RateLimit-Remaining
    maxAge: 86400
    allowCredentials: true
```

## Request/Response Transformation

### ClientTrafficPolicy - Headers

**File:** `gateway/client-traffic/headers.yaml`

```yaml
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: ClientTrafficPolicy
metadata:
  name: security-headers
  namespace: overmind-prod
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: Gateway
    name: overmind-gateway

  headers:
    response:
      add:
      - name: X-Frame-Options
        value: DENY
      - name: X-Content-Type-Options
        value: nosniff
      - name: X-XSS-Protection
        value: "1; mode=block"
      - name: Strict-Transport-Security
        value: max-age=31536000; includeSubDomains
      remove:
      - Server
      - X-Powered-By
```

## Circuit Breaking

### BackendTrafficPolicy - Circuit Breaker

**File:** `gateway/backend-traffic/circuit-breaker.yaml`

```yaml

apiVersion: gateway.envoyproxy.io/v1alpha1
kind: BackendTrafficPolicy
metadata:
  name: circuit-breaker
  namespace: overmind-prod
spec:
  targetRef:
    group: ""
    kind: Service
    name: overmind-api

  circuitBreaker:
    maxConnections: 1024
    maxPendingRequests: 1024
    maxRequests: 1024
    maxRetries: 3
```

## Timeouts and Retries

### BackendTrafficPolicy - Resilience

**File:** `gateway/backend-traffic/resilience.yaml`

```yaml
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: BackendTrafficPolicy
metadata:
  name: resilience
  namespace: overmind-prod
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: HTTPRoute
    name: api

  timeout:
    request: 30s
    backendRequest: 25s

  retry:
    numRetries: 3
    perRetryTimeout: 10s
    retryOn:
      httpStatusCodes:
      - 500
      - 502
      - 503
      - 504
      triggers:
      - connect-failure
      - retriable-4xx
```

## Observability

### EnvoyProxy - Telemetry

**File:** `gateway/envoy-proxy/telemetry.yaml`

```yaml

apiVersion: gateway.envoyproxy.io/v1alpha1
kind: EnvoyProxy
metadata:
  name: telemetry-config
  namespace: envoy-gateway-system
spec:
  telemetry:
    accessLog:
      settings:

      - format:
          type: JSON
          json:
            timestamp: "%START_TIME%"
            protocol: "%PROTOCOL%"
            method: "%REQ(:METHOD)%"
            path: "%REQ(X-ENVOY-ORIGINAL-PATH?:PATH)%"
            responseCode: "%RESPONSE_CODE%"
            duration: "%DURATION%"
            upstreamHost: "%UPSTREAM_HOST%"

    metrics:
      prometheus:
        disable: false

    tracing:
      provider:
        type: OpenTelemetry
        openTelemetry:
          host: jaeger-collector.observability.svc.cluster.local
          port: 4317
      samplingRate: 10
```

## Monitoring

### Prometheus Metrics

```bash
# Port forward Envoy admin interface
kubectl port-forward -n envoy-gateway-system \
  deployment/envoy-gateway 19000:19000

# Query metrics
curl http://localhost:19000/stats/prometheus

# Key metrics
# envoy_http_downstream_rq_total
# envoy_http_downstream_rq_xx (2xx, 4xx, 5xx)
# envoy_cluster_upstream_rq_time
# envoy_cluster_upstream_rq_retry
```

### Access Logs

```bash

# View Envoy proxy logs
kubectl logs -n envoy-gateway-system \
  -l gateway.envoyproxy.io/owning-gateway-name=overmind-gateway \
  --tail=100 -f
```

## Troubleshooting

### Gateway not ready

```bash
# Check Gateway status
kubectl describe gateway overmind-gateway -n overmind-prod

# Check Envoy deployment
kubectl get pods -n envoy-gateway-system

# Check events
kubectl get events -n overmind-prod --sort-by='.lastTimestamp'
```

### 404 errors

```bash

# Verify HTTPRoute
kubectl describe httproute api -n overmind-prod

# Check route status
kubectl get httproute -n overmind-prod -o yaml

# Test with verbose curl
curl -vH "Host: api.overmind.example.com" <http://<gateway-address>/api/health>
```

### Rate limiting not working

```bash
# Check RateLimitPolicy
kubectl describe ratelimitpolicy anonymous-rate-limit -n overmind-prod

# Test rate limit
for i in {1..15}; do
  curl -H "Host: api.overmind.example.com" http://<gateway-address>/api/health
done

# Should see 429 after 10 requests
```

### TLS certificate issues

```bash

# Verify secret exists
kubectl get secret overmind-tls -n overmind-prod

# Check certificate
kubectl get secret overmind-tls -n overmind-prod -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -text -noout
```

## Best Practices

1. **Use Gateway API** - Standard, portable across implementations
1. **Enable TLS** - Always terminate TLS at gateway
1. **Rate limit by route** - Different limits for different endpoints
1. **Add security headers** - Protect against common attacks
1. **Enable circuit breaking** - Prevent cascading failures
1. **Configure timeouts** - Don't wait forever for backends
1. **Use retries wisely** - Only for idempotent operations
1. **Monitor metrics** - Track request rates, errors, latencies

## Migration from nginx Ingress

### Step 1: Install Envoy Gateway alongside nginx

```bash
# Envoy Gateway uses different hostnames initially
# e.g., api-new.overmind.example.com
```

### Step 2: Test Envoy Gateway

```bash

# Verify all routes work

# Test rate limiting, CORS, etc.
```

### Step 3: Switch DNS

```bash
# Update DNS to point to Envoy Gateway
# Monitor for issues
```

### Step 4: Decommission nginx

```bash

# After successful migration
kubectl delete ingress --all -n overmind-prod
```

## References

- [Envoy Gateway Documentation](https://gateway.envoyproxy.io/)
- [Gateway API Specification](https://gateway-api.sigs.k8s.io/)
- [Envoy Proxy Documentation](https://www.envoyproxy.io/docs)
- [Rate Limiting Guide](https://gateway.envoyproxy.io/latest/user/rate-limit/)

## License

MIT
