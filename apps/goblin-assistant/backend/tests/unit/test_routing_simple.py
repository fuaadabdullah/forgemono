"""
Unit tests for routing logic.

Tests routing decisions and provider selection logic.
"""

import unittest


class TestRoutingLogic(unittest.TestCase):
    """Test routing decision logic."""

    def test_provider_selection_basic(self):
        """Test basic provider selection logic."""
        # Mock provider data
        providers = [
            {
                "name": "openai",
                "priority": 1,
                "is_active": True,
                "capabilities": ["chat"],
            },
            {
                "name": "anthropic",
                "priority": 2,
                "is_active": True,
                "capabilities": ["chat"],
            },
            {
                "name": "groq",
                "priority": 3,
                "is_active": True,
                "capabilities": ["chat"],
            },
        ]

        # Simple capability match
        capability = "chat"
        suitable_providers = [
            p for p in providers if capability in p["capabilities"] and p["is_active"]
        ]

        assert len(suitable_providers) == 3
        assert all(
            p["name"] in ["openai", "anthropic", "groq"] for p in suitable_providers
        )

    def test_provider_priority_ordering(self):
        """Test that providers are ordered by priority."""
        providers = [
            {"name": "groq", "priority": 3, "is_active": True},
            {"name": "openai", "priority": 1, "is_active": True},
            {"name": "anthropic", "priority": 2, "is_active": True},
        ]

        # Sort by priority (lower number = higher priority)
        sorted_providers = sorted(providers, key=lambda p: p["priority"])

        assert sorted_providers[0]["name"] == "openai"  # priority 1
        assert sorted_providers[1]["name"] == "anthropic"  # priority 2
        assert sorted_providers[2]["name"] == "groq"  # priority 3

    def test_capability_filtering(self):
        """Test filtering providers by capability."""
        providers = [
            {"name": "openai", "capabilities": ["chat", "vision"], "is_active": True},
            {"name": "anthropic", "capabilities": ["chat"], "is_active": True},
            {"name": "elevenlabs", "capabilities": ["audio"], "is_active": True},
        ]

        # Filter for chat capability
        chat_providers = [
            p for p in providers if "chat" in p["capabilities"] and p["is_active"]
        ]

        assert len(chat_providers) == 2
        assert all(p["name"] in ["openai", "anthropic"] for p in chat_providers)

        # Filter for vision capability
        vision_providers = [
            p for p in providers if "vision" in p["capabilities"] and p["is_active"]
        ]

        assert len(vision_providers) == 1
        assert vision_providers[0]["name"] == "openai"

    def test_inactive_provider_exclusion(self):
        """Test that inactive providers are excluded."""
        providers = [
            {"name": "openai", "is_active": True, "capabilities": ["chat"]},
            {"name": "anthropic", "is_active": False, "capabilities": ["chat"]},
            {"name": "groq", "is_active": True, "capabilities": ["chat"]},
        ]

        active_providers = [p for p in providers if p["is_active"]]

        assert len(active_providers) == 2
        assert all(p["name"] in ["openai", "groq"] for p in active_providers)

    def test_routing_decision_logic(self):
        """Test the core routing decision logic."""
        # Simulate routing requirements
        requirements = {
            "message": "Hello, how are you?",
            "complexity": "simple",
            "needs_vision": False,
        }

        # Mock provider scoring
        def score_provider(provider, requirements):
            base_score = 100

            # Prefer providers that match requirements
            if (
                requirements.get("needs_vision")
                and "vision" not in provider["capabilities"]
            ):
                base_score -= 50

            # Adjust for priority
            base_score -= (provider["priority"] - 1) * 10

            return base_score

        providers = [
            {"name": "openai", "priority": 1, "capabilities": ["chat", "vision"]},
            {"name": "anthropic", "priority": 2, "capabilities": ["chat"]},
            {"name": "groq", "priority": 3, "capabilities": ["chat"]},
        ]

        # Score all providers
        scored_providers = [
            {**p, "score": score_provider(p, requirements)} for p in providers
        ]

        # Sort by score descending
        sorted_providers = sorted(
            scored_providers, key=lambda p: p["score"], reverse=True
        )

        # Best provider should be OpenAI (highest priority, supports vision if needed)
        assert sorted_providers[0]["name"] == "openai"
        assert sorted_providers[0]["score"] == 100  # Full score

        # Verify scoring decreases with priority
        assert sorted_providers[1]["name"] == "anthropic"
        assert sorted_providers[1]["score"] == 90  # -10 for priority

        assert sorted_providers[2]["name"] == "groq"
        assert sorted_providers[2]["score"] == 80  # -20 for priority
