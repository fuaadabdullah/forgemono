"""
Raptor API Adapter for GoblinOS Assistant mini
Client for the Raptor Mini API backend
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional

try:
    import aiohttp
except Exception:
    aiohttp = None

from .base import (
    ModelAdapter,
    ModelConfig,
    ModelResponse,
    ModelProvider,
    ModelAdapterError,
    ModelCapability,
)

logger = logging.getLogger(__name__)


class RaptorApiAdapter(ModelAdapter):
    """
    Adapter for Raptor Mini API backend.
    Connects to the FastAPI server running Raptor Mini.
    """

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = (
            config.base_url or "https://thomasena-auxochromic-joziah.ngrok-free.dev"
        )

        # Ensure we have the right capabilities
        if ModelCapability.TEXT_GENERATION not in self.config.capabilities:
            self.config.capabilities.append(ModelCapability.TEXT_GENERATION)
        if ModelCapability.CODE_GENERATION not in self.config.capabilities:
            self.config.capabilities.append(ModelCapability.CODE_GENERATION)
        if ModelCapability.DOCUMENTATION not in self.config.capabilities:
            self.config.capabilities.append(ModelCapability.DOCUMENTATION)

    async def initialize(self) -> bool:
        """
        Initialize the API adapter.
        Creates HTTP session and verifies API connectivity.
        """
        try:
            if self.session:
                await self.session.close()

            if aiohttp is None:
                raise ModelAdapterError(
                    "aiohttp is not installed", self.provider, recoverable=False
                )
            # Create new session with timeout
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

            # Test connection (but don't fail if health check fails - API might still work)
            health_ok = await self.health_check()
            if health_ok:
                logger.info(f"Raptor API adapter initialized: {self.base_url}")
            else:
                logger.warning(f"Raptor API health check failed, but proceeding with initialization: {self.base_url}")
            
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Raptor API adapter: {e}")
            self._initialized = False
            return False

    async def generate(
        self, prompt: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> ModelResponse:
        """
        Generate text using the Raptor API.

        Args:
            prompt: Input prompt
            context: Additional context
            **kwargs: Additional parameters

        Returns:
            ModelResponse: Generated response
        """
        if not self._initialized or not self.session:
            raise ModelAdapterError("Adapter not initialized", self.provider)

        try:
            # Prepare API payload
            payload = {
                "task": "analyze_document",
                "content": prompt,
                "analysis_type": "quality_score",
            }

            # Add context if provided
            if context:
                if "task_type" in context:
                    payload["task"] = context["task_type"]
                if "analysis_type" in context:
                    payload["analysis_type"] = context["analysis_type"]

            start_time = time.time()

            async with self.session.post(
                f"{self.base_url}/analyze", json=payload
            ) as response:
                latency = time.time() - start_time

                if response.status != 200:
                    error_text = await response.text()
                    raise ModelAdapterError(
                        f"API error {response.status}: {error_text}", self.provider
                    )

                result = await response.json()

                # Update metrics
                self.metrics.request_count += 1
                self.metrics.total_latency += latency

                # Extract response content
                content = ""
                if "score" in result:
                    content = f"Quality Score: {result['score']}/100"
                    if "strength" in result:
                        content += f"\nStrength: {result['strength']}"
                    if "weakness" in result:
                        content += f"\nWeakness: {result['weakness']}"
                elif "content" in result:
                    content = result["content"]
                else:
                    content = str(result)

                return ModelResponse(
                    content=content,
                    provider=self.provider,
                    model_name=self.config.model_name,
                    tokens_used=None,  # API doesn't provide token counts
                    finish_reason="completed",
                    metadata={
                        "latency": latency,
                        "api_url": self.base_url,
                        "raw_response": result,
                    },
                )

        except aiohttp.ClientError as e:
            self.metrics.error_count += 1
            self.metrics.last_error = str(e)
            raise ModelAdapterError(
                f"Network error: {e}", self.provider, recoverable=True
            )
        except Exception as e:
            self.metrics.error_count += 1
            self.metrics.last_error = str(e)
            raise ModelAdapterError(f"Generation failed: {e}", self.provider)

    async def generate_code(
        self,
        task: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ModelResponse:
        """
        Generate code using the Raptor API.
        Uses specialized code generation prompts.
        """
        # Create a code generation prompt
        code_prompt = f"""Please generate {language} code for the following task:

Task: {task}

Requirements:
- Use proper {language} syntax and best practices
- Include helpful comments
- Handle errors appropriately
- Follow {language} conventions

Provide only the code without additional explanation."""

        # Add context
        enhanced_context = context or {}
        enhanced_context.update({"task_type": "code_generation", "language": language})

        return await self.generate(code_prompt, enhanced_context, **kwargs)

    async def review_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ModelResponse:
        """
        Review code using the Raptor API.
        """
        review_prompt = f"""Please review the following {language} code and provide constructive feedback:

``` {language}
{code}
```

Please provide:
1. Overall assessment
2. Specific issues or improvements needed
3. Best practices recommendations
4. Security considerations if applicable

Be specific and actionable in your feedback."""

        # Add context
        enhanced_context = context or {}
        enhanced_context.update({"task_type": "code_review", "language": language})

        return await self.generate(review_prompt, enhanced_context, **kwargs)

    async def health_check(self) -> bool:
        """Check if the Raptor API is healthy"""
        if not self.session:
            return False

        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception:
            return False

    async def cleanup(self) -> None:
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
        self._initialized = False

    def get_api_info(self) -> Dict[str, Any]:
        """Get information about the API connection"""
        return {
            "provider": self.provider.value,
            "base_url": self.base_url,
            "model_name": self.config.model_name,
            "capabilities": [cap.value for cap in self.config.capabilities],
            "initialized": self._initialized,
            "timeout": self.config.timeout,
        }
