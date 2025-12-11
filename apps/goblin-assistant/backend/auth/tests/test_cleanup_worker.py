import pytest
import asyncio
# no direct store factory import needed; use auth.router.challenge_store


@pytest.mark.asyncio
async def test_cleanup_expired_challenges(monkeypatch):
    # Ensure we use the in-memory store
    monkeypatch.setenv("USE_REDIS_CHALLENGES", "false")
    # Import auth router to get the cleanup function and challenge_store
    from auth.auth_router import cleanup_expired_challenges, challenge_store

    # Seed entries: one expired, one valid
    await challenge_store.set_challenge("a@x.com", "c1", expires_seconds=1)
    await challenge_store.set_challenge("b@x.com", "c2", expires_seconds=60)

    # Wait to let first entry expire
    await asyncio.sleep(1.2)

    removed = await cleanup_expired_challenges()
    assert removed >= 1
