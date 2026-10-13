import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from redis.exceptions import ConnectionError as RedisConnectionError
from starlette.requests import Request

from app.core.rate_limit import rate_limit


class FakeRedis:
    def __init__(self, result=(1, 0), error=None):
        self.result = result
        self.error = error
        self.calls = []

    async def eval(self, *args):
        self.calls.append(args)
        if self.error:
            raise self.error
        return self.result


def _request(redis_client=None, *, forwarded_for="198.51.100.5"):
    headers = []
    if forwarded_for:
        headers.append((b"x-forwarded-for", forwarded_for.encode()))
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": headers,
            "client": ("203.0.113.8", 1234),
            "server": ("testserver", 80),
            "app": SimpleNamespace(
                state=SimpleNamespace(rate_limit_redis=redis_client)
            ),
        }
    )


def test_rate_limit_counts_hashed_ip_and_user_keys():
    redis_client = FakeRedis()
    dependency = rate_limit("invite", limit=5, window_seconds=3600)

    asyncio.run(dependency(_request(redis_client), user={"id": "user-1"}))

    script, key_count, ip_key, user_key, window, limit = redis_client.calls[0]
    assert "INCR" in script
    assert key_count == 2
    assert "203.0.113.8" not in ip_key
    assert "user-1" not in user_key
    assert window == 3600
    assert limit == 5


def test_public_rate_limit_uses_direct_peer_ip_not_forwarded_header():
    redis_client = FakeRedis()
    dependency = rate_limit(
        "invitation-preview",
        limit=30,
        window_seconds=60,
        authenticated=False,
    )

    asyncio.run(dependency(_request(redis_client)))

    _, key_count, ip_key, window, limit = redis_client.calls[0]
    assert key_count == 1
    assert "198.51.100.5" not in ip_key
    assert window == 60
    assert limit == 30


def test_rate_limit_rejects_with_retry_after_header():
    dependency = rate_limit("invite", limit=5, window_seconds=3600)

    with pytest.raises(HTTPException) as raised:
        asyncio.run(
            dependency(
                _request(FakeRedis(result=(0, 42))),
                user={"id": "user-1"},
            )
        )

    assert raised.value.status_code == 429
    assert raised.value.headers["Retry-After"] == "42"


@pytest.mark.parametrize(
    "redis_client",
    [
        None,
        FakeRedis(error=RedisConnectionError("Redis unavailable")),
    ],
)
def test_rate_limit_fails_closed_when_redis_is_unavailable(redis_client):
    dependency = rate_limit("invite", limit=5, window_seconds=3600)

    with pytest.raises(HTTPException) as raised:
        asyncio.run(
            dependency(
                _request(redis_client),
                user={"id": "user-1"},
            )
        )

    assert raised.value.status_code == 503
    assert raised.value.headers["Retry-After"] == "5"
