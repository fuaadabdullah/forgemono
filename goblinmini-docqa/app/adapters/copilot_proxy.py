import os
import requests
import hashlib
import redis
from ..metrics import record_copilot_usage, record_copilot_error


class CopilotProxyAdapter:
    name = "copilot_proxy"

    def __init__(self, url: str = None, api_key: str = None, timeout: int = 30):
        self.url = url or os.getenv("COPILOT_API_URL")
        self.api_key = api_key or os.getenv("COPILOT_API_KEY")
        self.timeout = timeout
        self.redis_client = None
        self.token_budget_daily = int(
            os.getenv("COPILOT_TOKEN_BUDGET_DAILY", "100000")
        )  # 100k tokens/day default
        self.enable_cache = os.getenv("COPILOT_CACHE_ENABLED", "true").lower() == "true"

        # Initialize Redis for caching and budget tracking
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        except Exception:
            self.redis_client = None

    def init(self):
        # nothing heavy to init, but validate
        if not self.url or not self.api_key:
            raise RuntimeError("copilot proxy not configured")

    def health_check(self, timeout: float = 3.0) -> bool:
        try:
            response = requests.get(
                self.url + "/health",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=timeout,
            )
            return response.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, **kwargs):
        payload = {"prompt": prompt, **kwargs}
        response = requests.post(
            self.url + "/generate",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def analyze_content(self, content: str, filename: str = None):
        """Analyze document content via proxy with caching and budget control."""
        try:
            # Check token budget if Redis is available
            if self.redis_client and not self._check_token_budget():
                raise RuntimeError("Daily token budget exceeded")

            # Check cache first if enabled
            if self.enable_cache and self.redis_client:
                cache_key = self._get_cache_key(content, filename)
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    # Return cached result (no token cost)
                    import json

                    return json.loads(cached_result)

            payload = {"content": content, "filename": filename}
            response = requests.post(
                self.url + "/analyze/content",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()

            # Extract actual token usage from response if available
            tokens_used = self._extract_tokens_used(result, content)

            # Update token budget
            if self.redis_client:
                self._update_token_budget(tokens_used)

            # Cache successful results
            if self.enable_cache and self.redis_client and response.status_code == 200:
                cache_key = self._get_cache_key(content, filename)
                import json

                self.redis_client.setex(
                    cache_key, 3600, json.dumps(result)
                )  # Cache for 1 hour

            # Record Copilot usage metrics with actual token count
            record_copilot_usage("analyze_content", tokens_used, "analyze_content")

            return result

        except Exception:
            # Record Copilot error
            record_copilot_error("analyze_content", "api_error")
            raise

    def _extract_tokens_used(self, result, content: str) -> int:
        """Extract actual token usage from API response."""
        if isinstance(result, dict):
            # Check for usage info in response
            usage = result.get("usage", {})
            if isinstance(usage, dict):
                return usage.get("total_tokens", usage.get("tokens_used", 0))
            elif hasattr(result, "usage"):
                # Some APIs return usage as an object
                usage_obj = result.usage
                return getattr(
                    usage_obj,
                    "total_tokens",
                    getattr(usage_obj, "input_tokens", 0)
                    + getattr(usage_obj, "output_tokens", 0),
                )

        # Fallback to conservative estimation if no usage info
        # Use 6 chars per token (more conservative than 4)
        return max(1, len(content) // 6)

    def _get_cache_key(self, content: str, filename: str = None) -> str:
        """Generate cache key for content analysis."""
        key_data = f"{content}:{filename or 'unknown'}"
        return f"copilot_cache:{hashlib.sha256(key_data.encode()).hexdigest()}"

    def _check_token_budget(self) -> bool:
        """Check if daily token budget allows this request."""
        if not self.redis_client:
            return True  # Allow if no Redis

        try:
            import time

            today = time.strftime("%Y-%m-%d")
            used_key = f"copilot_used:{today}"

            used_tokens = int(self.redis_client.get(used_key) or 0)
            return used_tokens < self.token_budget_daily
        except Exception:
            return True  # Allow on error

    def _update_token_budget(self, tokens_used: int):
        """Update daily token usage counter."""
        if not self.redis_client:
            return

        try:
            import time

            today = time.strftime("%Y-%m-%d")
            used_key = f"copilot_used:{today}"

            # Increment usage (with expiry for automatic cleanup)
            self.redis_client.incrby(used_key, tokens_used)
            self.redis_client.expire(used_key, 86400 * 7)  # 7 days
        except Exception:
            pass  # Don't fail on budget tracking errors

    def metadata(self):
        return {"name": self.name, "type": "proxy", "url": self.url}

    def shutdown(self):
        pass
