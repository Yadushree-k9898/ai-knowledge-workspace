"""Shared Redis-backed rate limiting for sensitive API operations."""

import hashlib
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.modules.auth.dependencies import get_current_user

_CONSUME_LIMITS_SCRIPT = """
local retry_after = 0
for i, key in ipairs(KEYS) do
    local count = tonumber(redis.call('GET', key) or '0')
    if count >= tonumber(ARGV[2]) then
        local ttl = redis.call('TTL', key)
        if ttl > retry_after then
            retry_after = ttl
        end
    end
end
if retry_after > 0 then
    return {0, retry_after}
end
for i, key in ipairs(KEYS) do
    local count = redis.call('INCR', key)
    if count == 1 then
        redis.call('EXPIRE', key, tonumber(ARGV[1]))
    end
end
return {1, 0}
"""


def _limit_key(scope: str, identity_type: str, identity: str) -> str:
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return f"rate-limit:{scope}:{identity_type}:{digest}"


async def _enforce_limit(
    request: Request,
    *,
    scope: str,
    limit: int,
    window_seconds: int,
    user_id: str | None,
) -> None:
    redis_client: Redis | None = getattr(request.app.state, "rate_limit_redis", None)
    if redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting is temporarily unavailable. Please try again later.",
            headers={"Retry-After": "5"},
        )

    client_ip = request.client.host if request.client else "unknown"
    keys = [_limit_key(scope, "ip", client_ip)]
    if user_id is not None:
        keys.append(_limit_key(scope, "user", user_id))

    try:
        allowed, retry_after = await redis_client.eval(
            _CONSUME_LIMITS_SCRIPT,
            len(keys),
            *keys,
            window_seconds,
            limit,
        )
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting is temporarily unavailable. Please try again later.",
            headers={"Retry-After": "5"},
        ) from exc

    if not allowed:
        retry_after = max(int(retry_after), 1)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def rate_limit(
    scope: str,
    *,
    limit: int,
    window_seconds: int,
    authenticated: bool = True,
) -> Callable:
    """Create a dependency that enforces shared IP and optional per-user limits."""
    if authenticated:
        async def enforce_authenticated(
            request: Request,
            user: dict = Depends(get_current_user),
        ) -> None:
            await _enforce_limit(
                request,
                scope=scope,
                limit=limit,
                window_seconds=window_seconds,
                user_id=user["id"],
            )

        return enforce_authenticated

    async def enforce_by_ip(request: Request) -> None:
        await _enforce_limit(
            request,
            scope=scope,
            limit=limit,
            window_seconds=window_seconds,
            user_id=None,
        )

    return enforce_by_ip
