"""
ChatProviderSelector Service for selecting and configuring providers.

This service handles provider selection and configuration for chat completion requests,
separating provider management concerns from the main chat handler.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderPriority(Enum):
    """Provider priority levels."""

    HIGH = 1
    MEDIUM = 2
    LOW = 3
    DISABLED = 999


@dataclass
class ProviderConfig:
    """Configuration for a provider."""

    name: str
    model: str
    priority: ProviderPriority
    enabled: bool
    weight: float = 1.0
    max_concurrent_requests: int = 10
    timeout_seconds: int = 30
    retry_attempts: int = 3
    fallback_providers: List[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ProviderScore:
    """Score for a provider."""

    provider_name: str
    score: float
    factors: Dict[str, float]
    last_used: Optional[float] = None
    error_rate: float = 0.0
    avg_response_time: float = 0.0


class ChatProviderSelector:
    """Service for selecting and configuring providers."""

    def __init__(self, providers: List[ProviderConfig]):
        """Initialize the ChatProviderSelector."""
        self.providers = {p.name: p for p in providers}
        self.provider_scores: Dict[str, ProviderScore] = {}
        self.provider_usage: Dict[str, int] = {}
        self.provider_errors: Dict[str, int] = {}
        self.provider_response_times: Dict[str, List[float]] = {}

        # Initialize scores
        for provider_name in self.providers:
            self.provider_scores[provider_name] = ProviderScore(
                provider_name=provider_name,
                score=0.0,
                factors={},
                last_used=None,
                error_rate=0.0,
                avg_response_time=0.0,
            )
            self.provider_usage[provider_name] = 0
            self.provider_errors[provider_name] = 0
            self.provider_response_times[provider_name] = []

    async def select_provider(
        self, model: str, messages: List[Dict[str, Any]], chat_state: "ChatState"
    ) -> Optional[ProviderConfig]:
        """
        Select the best provider for a chat request.

        Args:
            model: Model to use for generation
            messages: List of chat messages
            chat_state: Current chat state

        Returns:
            Best provider configuration, or None if no suitable provider found
        """
        try:
            # Get available providers for this model
            available_providers = self._get_available_providers(model)

            if not available_providers:
                logger.warning(f"No available providers for model: {model}")
                return None

            # Calculate scores for available providers
            scored_providers = []
            for provider_name in available_providers:
                score = self._calculate_provider_score(
                    provider_name, model, messages, chat_state
                )
                scored_providers.append((provider_name, score))

            # Sort by score (highest first)
            scored_providers.sort(key=lambda x: x[1].score, reverse=True)

            # Select best provider
            best_provider_name = scored_providers[0][0]
            best_provider = self.providers[best_provider_name]

            # Update usage tracking
            self._update_provider_usage(best_provider_name)

            logger.info(
                f"Selected provider '{best_provider_name}' for model '{model}' with score {scored_providers[0][1].score}"
            )

            return best_provider

        except Exception as e:
            logger.error(f"Error selecting provider for model {model}: {e}")
            return None

    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """
        Get configuration for a specific provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Provider configuration, or None if not found
        """
        return self.providers.get(provider_name)

    def update_provider_score(
        self, provider_name: str, response_time: float, success: bool
    ) -> None:
        """
        Update provider score based on performance.

        Args:
            provider_name: Name of the provider
            response_time: Response time in seconds
            success: Whether the request was successful
        """
        try:
            if provider_name not in self.provider_scores:
                return

            score = self.provider_scores[provider_name]

            # Update error tracking
            if not success:
                self.provider_errors[provider_name] += 1

            # Update response time tracking
            self.provider_response_times[provider_name].append(response_time)
            if (
                len(self.provider_response_times[provider_name]) > 100
            ):  # Keep last 100 measurements
                self.provider_response_times[provider_name].pop(0)

            # Recalculate metrics
            total_requests = self.provider_usage[provider_name]
            error_count = self.provider_errors[provider_name]
            response_times = self.provider_response_times[provider_name]

            score.error_rate = error_count / max(total_requests, 1)
            score.avg_response_time = (
                sum(response_times) / max(len(response_times), 1)
                if response_times
                else 0.0
            )
            score.last_used = time.time()

            # Recalculate overall score
            score.score = self._calculate_overall_score(score)

            logger.debug(f"Updated score for provider '{provider_name}': {score.score}")

        except Exception as e:
            logger.error(f"Error updating provider score for {provider_name}: {e}")

    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers."""
        try:
            stats = {}

            for provider_name, provider in self.providers.items():
                score = self.provider_scores[provider_name]
                response_times = self.provider_response_times[provider_name]

                stats[provider_name] = {
                    "config": {
                        "name": provider.name,
                        "model": provider.model,
                        "priority": provider.priority.value,
                        "enabled": provider.enabled,
                        "weight": provider.weight,
                        "max_concurrent_requests": provider.max_concurrent_requests,
                        "timeout_seconds": provider.timeout_seconds,
                        "retry_attempts": provider.retry_attempts,
                    },
                    "metrics": {
                        "usage_count": self.provider_usage[provider_name],
                        "error_count": self.provider_errors[provider_name],
                        "error_rate": score.error_rate,
                        "avg_response_time": score.avg_response_time,
                        "last_used": score.last_used,
                        "score": score.score,
                        "response_time_samples": len(response_times),
                    },
                }

            return stats

        except Exception as e:
            logger.error(f"Error getting provider stats: {e}")
            return {}

    def enable_provider(self, provider_name: str) -> bool:
        """Enable a provider."""
        try:
            if provider_name not in self.providers:
                return False

            self.providers[provider_name].enabled = True
            logger.info(f"Enabled provider: {provider_name}")
            return True

        except Exception as e:
            logger.error(f"Error enabling provider {provider_name}: {e}")
            return False

    def disable_provider(self, provider_name: str) -> bool:
        """Disable a provider."""
        try:
            if provider_name not in self.providers:
                return False

            self.providers[provider_name].enabled = False
            logger.info(f"Disabled provider: {provider_name}")
            return True

        except Exception as e:
            logger.error(f"Error disabling provider {provider_name}: {e}")
            return False

    def update_provider_priority(
        self, provider_name: str, priority: ProviderPriority
    ) -> bool:
        """Update provider priority."""
        try:
            if provider_name not in self.providers:
                return False

            self.providers[provider_name].priority = priority
            logger.info(f"Updated priority for provider {provider_name}: {priority}")
            return True

        except Exception as e:
            logger.error(f"Error updating provider priority for {provider_name}: {e}")
            return False

    def get_fallback_providers(self, provider_name: str) -> List[str]:
        """Get fallback providers for a given provider."""
        try:
            if provider_name not in self.providers:
                return []

            provider = self.providers[provider_name]
            return provider.fallback_providers or []

        except Exception as e:
            logger.error(f"Error getting fallback providers for {provider_name}: {e}")
            return []

    def reset_provider_stats(self, provider_name: Optional[str] = None) -> None:
        """Reset statistics for a provider or all providers."""
        try:
            if provider_name:
                if provider_name in self.provider_scores:
                    self.provider_scores[provider_name] = ProviderScore(
                        provider_name=provider_name,
                        score=0.0,
                        factors={},
                        last_used=None,
                        error_rate=0.0,
                        avg_response_time=0.0,
                    )
                    self.provider_usage[provider_name] = 0
                    self.provider_errors[provider_name] = 0
                    self.provider_response_times[provider_name] = []
                    logger.info(f"Reset stats for provider: {provider_name}")
            else:
                # Reset all providers
                for provider_name in self.providers:
                    self.provider_scores[provider_name] = ProviderScore(
                        provider_name=provider_name,
                        score=0.0,
                        factors={},
                        last_used=None,
                        error_rate=0.0,
                        avg_response_time=0.0,
                    )
                    self.provider_usage[provider_name] = 0
                    self.provider_errors[provider_name] = 0
                    self.provider_response_times[provider_name] = []
                logger.info("Reset stats for all providers")

        except Exception as e:
            logger.error(f"Error resetting provider stats: {e}")

    def _get_available_providers(self, model: str) -> List[str]:
        """Get list of available providers for a model."""
        available = []

        for provider_name, provider in self.providers.items():
            if (
                provider.enabled
                and provider.model == model
                and self._is_provider_healthy(provider_name)
            ):
                available.append(provider_name)

        return available

    def _is_provider_healthy(self, provider_name: str) -> bool:
        """Check if a provider is healthy (not overloaded or failing)."""
        try:
            score = self.provider_scores[provider_name]

            # Check error rate
            if score.error_rate > 0.5:  # More than 50% error rate
                logger.warning(
                    f"Provider {provider_name} has high error rate: {score.error_rate}"
                )
                return False

            # Check response time
            if score.avg_response_time > 30.0:  # More than 30 seconds average
                logger.warning(
                    f"Provider {provider_name} has high response time: {score.avg_response_time}"
                )
                return False

            # Check if recently used (avoid providers that haven't been used recently)
            if score.last_used and (time.time() - score.last_used) > 3600:  # 1 hour
                logger.debug(f"Provider {provider_name} hasn't been used recently")

            return True

        except Exception as e:
            logger.error(f"Error checking provider health for {provider_name}: {e}")
            return False

    def _calculate_provider_score(
        self,
        provider_name: str,
        model: str,
        messages: List[Dict[str, Any]],
        chat_state: "ChatState",
    ) -> ProviderScore:
        """Calculate score for a provider."""
        try:
            provider = self.providers[provider_name]
            score = self.provider_scores[provider_name]

            factors = {}

            # Base score from priority
            factors["priority"] = 10.0 / provider.priority.value

            # Weight factor
            factors["weight"] = provider.weight

            # Usage factor (prefer less used providers for load balancing)
            total_usage = sum(self.provider_usage.values())
            usage_factor = 1.0
            if total_usage > 0:
                usage_factor = 1.0 - (self.provider_usage[provider_name] / total_usage)
            factors["usage"] = usage_factor * 5.0

            # Performance factors
            factors["error_rate"] = max(
                0, 10.0 - (score.error_rate * 20.0)
            )  # Penalize high error rates
            factors["response_time"] = max(
                0, 10.0 - (score.avg_response_time / 3.0)
            )  # Penalize slow response times

            # Recency factor (prefer recently used providers)
            if score.last_used:
                time_since_used = time.time() - score.last_used
                factors["recency"] = max(
                    0, 5.0 - (time_since_used / 3600)
                )  # Decay over hours
            else:
                factors["recency"] = 1.0

            # Calculate overall score
            overall_score = sum(factors.values())

            # Update score object
            score.score = overall_score
            score.factors = factors

            return score

        except Exception as e:
            logger.error(f"Error calculating provider score for {provider_name}: {e}")
            return ProviderScore(
                provider_name=provider_name,
                score=0.0,
                factors={},
                last_used=None,
                error_rate=0.0,
                avg_response_time=0.0,
            )

    def _calculate_overall_score(self, score: ProviderScore) -> float:
        """Calculate overall score from individual factors."""
        return sum(score.factors.values())

    def _update_provider_usage(self, provider_name: str) -> None:
        """Update provider usage count."""
        self.provider_usage[provider_name] += 1
        self.provider_scores[provider_name].last_used = time.time()

    def get_best_provider_for_model(self, model: str) -> Optional[str]:
        """Get the best provider name for a specific model."""
        try:
            available_providers = self._get_available_providers(model)
            if not available_providers:
                return None

            # Get scores for available providers
            scored_providers = []
            for provider_name in available_providers:
                score = self.provider_scores[provider_name]
                scored_providers.append((provider_name, score.score))

            # Return the provider with highest score
            scored_providers.sort(key=lambda x: x[1], reverse=True)
            return scored_providers[0][0]

        except Exception as e:
            logger.error(f"Error getting best provider for model {model}: {e}")
            return None

    def get_provider_health_status(self, provider_name: str) -> Dict[str, Any]:
        """Get health status for a specific provider."""
        try:
            if provider_name not in self.providers:
                return {"error": "Provider not found"}

            provider = self.providers[provider_name]
            score = self.provider_scores[provider_name]

            return {
                "provider_name": provider_name,
                "enabled": provider.enabled,
                "priority": provider.priority.value,
                "usage_count": self.provider_usage[provider_name],
                "error_count": self.provider_errors[provider_name],
                "error_rate": score.error_rate,
                "avg_response_time": score.avg_response_time,
                "last_used": score.last_used,
                "score": score.score,
                "healthy": self._is_provider_healthy(provider_name),
                "metadata": provider.metadata,
            }

        except Exception as e:
            logger.error(
                f"Error getting provider health status for {provider_name}: {e}"
            )
            return {"error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """
        Get provider selector statistics.

        Returns:
            Dict containing provider statistics
        """
        return {
            "provider_scores": {
                name: score.score for name, score in self.provider_scores.items()
            },
            "provider_usage": self.provider_usage.copy(),
            "provider_errors": self.provider_errors.copy(),
            "provider_response_times": {
                name: sum(times) / len(times) if times else 0
                for name, times in self.provider_response_times.items()
            },
            "timestamp": time.time(),
        }
