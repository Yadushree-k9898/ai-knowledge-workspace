# Rate limiting

The API applies rate limiting to sensitive operations using atomic Redis
fixed-window counters shared across application workers. The limiter evaluates
both the authenticated user identity and the direct peer IP for protected user
requests, while unauthenticated invitation previews are limited by the direct
peer IP alone. The enforcement is fail-closed at the decision point: if either
counter is already exhausted, the request is rejected before the system records
any increment. This prevents partial, inconsistent state when a client exceeds
limits across multiple dimensions.

The exact scope, thresholds, response behavior, and covered endpoints are
specified in [Rate limits API notes](../api/rate-limits.md). Over-limit
requests return `429 Too Many Requests` with a `Retry-After` header; if Redis
becomes unavailable, the service returns `503 Service Unavailable` rather than
silently disabling protection. Redis is provisioned through the existing
`REDIS_URL`, so no additional rate-limit package or separate infrastructure is
required.

This design intentionally avoids trusting arbitrary forwarded IP headers. The
API reads the direct peer address from the transport layer and treats proxies or
load balancers as enforcers only when they are configured to supply the client
IP reliably. In production deployments behind a reverse proxy, the trusted edge
must enforce client-IP rate limits before requests reach the application
service.

Supabase Auth handles browser sign-in, sign-up, OAuth, and password recovery
directly, so those limits must be configured in Supabase rather than in the
application API. The API therefore only protects its own operations and does not
attempt to control external authentication-provider behavior.
