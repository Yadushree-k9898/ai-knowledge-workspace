# API rate limits

The API applies fixed-window limits using shared Redis counters. Authenticated
requests are checked against both the authenticated user ID and the direct
client IP. The Redis operation is atomic across both counters, so an exceeded
request does not consume the other counter. User and IP values are hashed
before being included in Redis keys.

| Operation | Limit |
| --- | ---: |
| Create organization | 5 per hour |
| Create project | 20 per hour |
| Create invitation | 5 per hour |
| Preview invitation | 30 per minute per IP |
| Accept invitation | 10 per hour |
| Bootstrap profile | 10 per hour |
| Update profile | 20 per hour |
| Upload document | 20 per hour |
| Create comparison | 10 per hour |
| Create report | 10 per hour |
| Regenerate report | 10 per hour |

When a limit is exceeded, the API responds with `429 Too Many Requests` and a
`Retry-After` header containing seconds until the fixed window expires. If the
limiter cannot reach Redis, the operation responds with `503 Service
Unavailable` and `Retry-After: 5`; the API does not silently skip enforcement.
Redis is initialized from the existing `REDIS_URL` setting.

## Supabase Auth

Browser sign-in, sign-up, Google OAuth, and password recovery communicate
directly with Supabase Auth rather than FastAPI. Configure their request and
email limits in the Supabase project; the FastAPI Redis limiter cannot enforce
limits on traffic that bypasses the API.

## Reverse proxies

The API does not trust caller-supplied `X-Forwarded-For` headers for rate-limit
identity. Behind a reverse proxy, apply appropriate per-client limits at the
trusted proxy/edge. Authenticated requests also have a user-based counter.
