import asyncio
import pytest

from auth.challenge_store import (
    InMemoryChallengeStore,
    get_challenge_store_instance,
)


@pytest.mark.asyncio
async def test_inmemory_challenge_store_set_get_delete_and_cleanup():
    store = InMemoryChallengeStore()
    email = "user@example.com"
    challenge = "test-challenge"

    # Set a short-lived challenge
    await store.set_challenge(email, challenge, expires_seconds=1)
    val = await store.get_challenge(email)
    assert val == challenge

    # Wait to expire
    await asyncio.sleep(1.2)
    val_after = await store.get_challenge(email)
    assert val_after is None

    # Cleanup should remove expired entries and return count
    # Add two entries and expire one
    await store.set_challenge("a@example.com", "c1", expires_seconds=0)
    await store.set_challenge("b@example.com", "c2", expires_seconds=60)
    removed = await store.cleanup_expired()
    assert removed >= 1


def test_get_challenge_store_instance_inmemory(monkeypatch):
    monkeypatch.delenv("USE_REDIS_CHALLENGES", raising=False)
    import importlib

    # force module reload to pick up env changes
    importlib.reload(__import__("auth.challenge_store", fromlist=["*"]))
    store = get_challenge_store_instance()
    from auth.challenge_store import InMemoryChallengeStore as IMC

    assert isinstance(store, IMC)


@pytest.mark.asyncio
async def test_cleanup_expired_challenges_via_auth_router(monkeypatch):
    # Use the real in-memory store via the factory and ensure cleanup_expired_challenges
    from auth import auth_router

    # Replace the challenge_store with a fresh in-memory instance for test isolation
    from auth.challenge_store import InMemoryChallengeStore

    store = InMemoryChallengeStore()
    auth_router.challenge_store = store

    # Set an expired challenge
    await store.set_challenge("x@example.com", "expired", expires_seconds=0)
    # Call cleanup from router wrapper
    count = await auth_router.cleanup_expired_challenges()
    assert count >= 1
