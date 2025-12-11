"""
Local Model Adapter for GoblinOS Assistant mini
Handles local AI model inference using llama.cpp or similar backends
"""

import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from .base import (
    ModelAdapter,
    ModelConfig,
    ModelResponse,
    ModelProvider,
    ModelAdapterError,
    ModelCapability,
)

logger = logging.getLogger(__name__)


class LocalModelAdapter(ModelAdapter):
    """
    Adapter for local AI model inference.
    Supports llama.cpp and similar local model servers.
    """

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.process: Optional[subprocess.Popen] = None
        self.server_url: Optional[str] = None
        self.model_path: Optional[Path] = None

        # Extract local-specific config
        self.model_path = Path(config.model_name) if config.model_name else None
        self.server_url = config.base_url or "http://localhost:8080"

    async def initialize(self) -> bool:
        """
        Initialize the local model adapter.
        Starts the local model server if not already running.
        """
        try:
            if not self.model_path or not self.model_path.exists():
                logger.warning(f"Model path not found: {self.model_path}")
                self._initialized = False
                return False

            # Check if server is already running
            if await self._check_server_health():
                logger.info("Local model server already running")
                self._initialized = True
                return True

            # Start the local model server
            await self._start_model_server()
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize local model adapter: {e}")
            self._initialized = False
            return False

    async def _check_server_health(self) -> bool:
        """Check if the local model server is responding"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.server_url}/health", timeout=5
                ) as response:
                    return response.status == 200
        except Exception:
            return False

    async def _start_model_server(self) -> None:
        """
        Start the local model server using llama.cpp or similar.
        This is a placeholder - actual implementation would depend on the specific backend.
        """
        # This is a simplified example. In practice, you'd start llama.cpp server
        # or another local inference server

        logger.info(f"Starting local model server for {self.model_path}")

        # Example command for llama.cpp server (would need to be adapted)
        cmd = [
            "llama.cpp/main",  # Path to llama.cpp executable
            "-m",
            str(self.model_path),
            "--host",
            "127.0.0.1",
            "--port",
            "8080",
            "--ctx-size",
            "2048",
            "--threads",
            "4",
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.model_path.parent if self.model_path else None,
            )

            # Wait for server to start
            await asyncio.sleep(2)

            # Verify server is running
            if not await self._check_server_health():
                raise ModelAdapterError(
                    "Local model server failed to start",
                    self.provider,
                    recoverable=False,
                )

            logger.info("Local model server started successfully")

        except Exception as e:
            logger.error(f"Failed to start local model server: {e}")
            if self.process:
                self.process.terminate()
                self.process = None
            raise ModelAdapterError(
                f"Server startup failed: {e}", self.provider, recoverable=False
            )

    async def generate(
        self, prompt: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> ModelResponse:
        """
        Generate text using the local model.

        Args:
            prompt: Input prompt
            context: Additional context
            **kwargs: Additional parameters

        Returns:
            ModelResponse: Generated response
        """
        if not self._initialized:
            raise ModelAdapterError("Adapter not initialized", self.provider)

        try:
            import aiohttp

            # Prepare request payload
            payload = {
                "prompt": prompt,
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "stream": False,
            }

            # Add context if provided
            if context:
                if "system_message" in context:
                    payload["system_message"] = context["system_message"]
                if "conversation_history" in context:
                    payload["messages"] = context["conversation_history"]

            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/completion",
                    json=payload,
                    timeout=self.config.timeout,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ModelAdapterError(
                            f"API error {response.status}: {error_text}", self.provider
                        )

                    result = await response.json()
                    latency = time.time() - start_time

                    # Update metrics
                    self.metrics.request_count += 1
                    self.metrics.total_latency += latency
                    if "usage" in result:
                        self.metrics.total_tokens += result["usage"].get(
                            "total_tokens", 0
                        )

                    return ModelResponse(
                        content=result.get("content", ""),
                        provider=self.provider,
                        model_name=self.config.model_name,
                        tokens_used=result.get("usage", {}).get("total_tokens"),
                        finish_reason=result.get("finish_reason"),
                        metadata={
                            "latency": latency,
                            "model_path": str(self.model_path),
                        },
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
        Generate code using the local model with coding-specific prompts.
        """
        # Create a coding-specific prompt
        code_prompt = f"""You are an expert {language} developer. Generate high-quality, well-documented code for the following task:

Task: {task}

Requirements:
- Use proper {language} syntax and best practices
- Include comments explaining the code
- Handle edge cases and errors appropriately
- Follow language-specific conventions

Please provide only the code without additional explanation:"""

        # Add context if provided
        if context:
            if "existing_code" in context:
                code_prompt += (
                    f"\n\nExisting code to work with:\n{context['existing_code']}"
                )
            if "requirements" in context:
                code_prompt += (
                    f"\n\nAdditional requirements:\n{context['requirements']}"
                )

        return await self.generate(code_prompt, context, **kwargs)

    async def review_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ModelResponse:
        """
        Review code using the local model.
        """
        review_prompt = f"""You are an expert {language} code reviewer. Please review the following code and provide constructive feedback:

``` {language}
{code}
```

Please provide:
1. Overall assessment
2. Specific issues or improvements
3. Best practices recommendations
4. Security considerations (if applicable)

Be specific and actionable in your feedback:"""

        return await self.generate(review_prompt, context, **kwargs)

    async def health_check(self) -> bool:
        """Check if the local model server is healthy"""
        return await self._check_server_health()

    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.process:
            logger.info("Stopping local model server")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None

        self._initialized = False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "provider": self.provider.value,
            "model_path": str(self.model_path) if self.model_path else None,
            "server_url": self.server_url,
            "capabilities": [cap.value for cap in self.config.capabilities],
            "initialized": self._initialized,
        }
