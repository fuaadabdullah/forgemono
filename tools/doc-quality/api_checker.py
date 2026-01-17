"""
API-Based Quality Checker

This module contains the DocQualityChecker class that provides
documentation quality analysis using the Raptor Mini API with various modes.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

from standalone_checker import StandaloneQualityChecker
from http_client import HTTPClient
from adapter_manager import AdapterManager


class DocQualityChecker:
    """Documentation quality checker using Raptor Mini API"""

    def __init__(
        self,
        api_url: str = "https://thomasena-auxochromic-joziah.ngrok-free.dev",
        debug_api: bool = False,
        debug_timing: bool = False,
        save_responses_dir: Optional[str] = None,
        mode: Optional[str] = None,
        config_file: Optional[str] = None,
        soft_fallback: Optional[bool] = False,
    ):
        # Initialize HTTP client
        self.http_client = HTTPClient(
            api_url=api_url,
            debug_api=debug_api,
            debug_timing=debug_timing,
            save_responses_dir=save_responses_dir,
        )

        # Initialize adapter manager
        self.adapter_manager = AdapterManager(
            mode=mode,
            config_file=config_file,
            soft_fallback=soft_fallback,
            api_url=api_url,
        )

        # Set mode and initialize adapters
        self.mode = mode or os.environ.get("RAPTOR_MODE", "dual")
        if self.mode == "standalone":
            # For standalone mode, try to initialize local LLM adapters
            self.adapter_manager.init_adapter_engine()
        else:
            self.adapter_manager.init_adapter_engine()

        # Initialize standalone checker as final fallback
        self.standalone_checker = StandaloneQualityChecker()

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single file"""
        # For standalone mode, try local LLM first, then fallback to heuristic
        if self.mode == "standalone":
            # Try local LLM adapter first
            if (
                hasattr(self.adapter_manager, "adapter_engine")
                and self.adapter_manager.adapter_engine
            ):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Initialize and generate in the same event loop
                    async def init_and_generate():
                        try:
                            if not getattr(
                                self.adapter_manager.adapter_engine,
                                "_initialized",
                                False,
                            ):
                                await self.adapter_manager.adapter_engine.initialize()
                            return await self.adapter_manager.adapter_engine.generate(
                                content,
                                context={"filename": file_path, "mode": self.mode},
                            )
                        finally:
                            # Ensure proper cleanup of adapter resources
                            await self.adapter_manager.adapter_engine.cleanup()

                    result_obj = asyncio.run(init_and_generate())
                    result = self._model_response_to_dict(
                        result_obj, filename=file_path
                    )
                    return result
                except Exception as e:
                    self.logger.debug(f"Local LLM analysis failed: {e}")
                    # Fall back to heuristic analyzer

            # Use heuristic analyzer as fallback
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                return self.standalone_checker.analyze_content(
                    content, filename=file_path
                )
            except Exception as e:
                return {
                    "error": f"Standalone analysis failed: {str(e)}",
                    "file_path": file_path,
                    "score": 0,
                }

        # Convert to absolute path relative to repo root
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        abs_file_path = os.path.abspath(os.path.join(repo_root, file_path))
        # If we are in phi_only mode but no adapter engine initialized, return error
        if self.mode == "phi_only" and not self.adapter_engine:
            return {
                "error": "Phi adapter not available",
                "file_path": file_path,
                "score": 0,
            }

        # If we have an adapter engine configured for local/dual mode, use it
        if self.adapter_engine and self.mode in ("phi_only", "dual"):
            try:
                with open(abs_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Initialize and generate in the same event loop
                async def init_and_generate():
                    try:
                        if not getattr(self.adapter_engine, "_initialized", False):
                            await self.adapter_engine.initialize()
                        return await self.adapter_engine.generate(
                            content, context={"filename": file_path, "mode": self.mode}
                        )
                    finally:
                        # Ensure proper cleanup of adapter resources
                        await self.adapter_engine.cleanup()

                result_obj = asyncio.run(init_and_generate())
                result = self._model_response_to_dict(result_obj, filename=file_path)
                return result
            except Exception as e:
                self.logger.debug(f"Adapter analysis failed: {e}")
                if self.mode == "phi_only":
                    return {
                        "error": f"Phi adapter error: {str(e)}",
                        "file_path": file_path,
                        "score": 0,
                    }

        payload = {"file_path": abs_file_path, "analysis_type": "quality_score"}
        try:
            response = self.http_client.make_request(
                "POST", "/analyze/file", json=payload, timeout=15
            )
            if response.status_code == 200:
                result = response.json()
                result["file_path"] = file_path  # Keep original path in result
                return result
            else:
                return {
                    "error": f"API error: {response.status_code}",
                    "file_path": file_path,
                    "score": 0,
                }
        except Exception as e:
            return {
                "error": f"Request failed: {str(e)}",
                "file_path": file_path,
                "score": 0,
            }

        # Final fallback: use standalone checker
        try:
            with open(abs_file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return self.standalone_checker.analyze_content(content, filename=file_path)
        except Exception as e:
            return {
                "error": f"All analysis methods failed: {str(e)}",
                "file_path": file_path,
                "score": 0,
            }

    def analyze_content(
        self, content: str, filename: str = "content.md"
    ) -> Dict[str, Any]:
        """Analyze content directly"""
        # For standalone mode, try local LLM first, then fallback to heuristic
        if self.mode == "standalone":
            # Try local LLM adapter first
            if hasattr(self, "adapter_engine") and self.adapter_engine:
                try:
                    # Initialize and generate in the same event loop
                    async def init_and_generate():
                        try:
                            if not getattr(self.adapter_engine, "_initialized", False):
                                await self.adapter_engine.initialize()
                            return await self.adapter_engine.generate(
                                content,
                                context={"filename": filename, "mode": self.mode},
                            )
                        finally:
                            # Ensure proper cleanup of adapter resources
                            await self.adapter_engine.cleanup()

                    result_obj = asyncio.run(init_and_generate())
                    return self._model_response_to_dict(result_obj, filename=filename)
                except Exception as e:
                    self.logger.debug(f"Local LLM analysis failed: {e}")
                    # Fall back to heuristic analyzer

            # Use heuristic analyzer as fallback
            return self.standalone_checker.analyze_content(content, filename=filename)
        # If we have an adapter engine, use it (supports phi_only, dual)
        if self.mode == "phi_only" and not self.adapter_engine:
            return {
                "error": "Phi adapter not available",
                "filename": filename,
                "score": 0,
            }

        if self.adapter_engine and self.mode in ("phi_only", "dual"):
            try:
                # Initialize and generate in the same event loop
                async def init_and_generate():
                    try:
                        if not getattr(self.adapter_engine, "_initialized", False):
                            await self.adapter_engine.initialize()
                        return await self.adapter_engine.generate(
                            content, context={"filename": filename, "mode": self.mode}
                        )
                    finally:
                        # Ensure proper cleanup of adapter resources
                        await self.adapter_engine.cleanup()

                result_obj = asyncio.run(init_and_generate())
                return self._model_response_to_dict(result_obj, filename=filename)
            except Exception as e:
                self.logger.debug(f"Adapter analysis failed: {e}")
                if self.mode == "phi_only":
                    return {
                        "error": f"Phi adapter error: {str(e)}",
                        "filename": filename,
                        "score": 0,
                    }

        payload = {
            "task": "analyze_document",
            "content": content,
            "analysis_type": "quality_score",
        }

        try:
            response = self.http_client.make_request(
                "POST", "/analyze", json=payload, timeout=15
            )
            if response.status_code == 200:
                result = response.json()
                result["filename"] = filename
                return result
            else:
                return {
                    "error": f"API error: {response.status_code}",
                    "filename": filename,
                    "score": 0,
                }
        except Exception as e:
            return {
                "error": f"Request failed: {str(e)}",
                "filename": filename,
                "score": 0,
            }

        # Final fallback: use standalone checker
        return self.standalone_checker.analyze_content(content, filename=filename)

    def set_adapter_engine(self, engine):
        """Set adapter engine directly (useful for tests and custom wiring)."""
        self.adapter_engine = engine

    def _parse_score_from_text(self, text: str) -> Optional[float]:
        """Parse a numeric score from text (e.g., 'Score: 73/100')"""
        try:
            import re

            m = re.search(r"Score[:\s]+(\d+(?:\.\d+)?)\/?100", text)
            if m:
                return float(m.group(1))
            # try to find just a plain number out of 100
            m2 = re.search(r"(\d+(?:\.\d+)?)\s*\/\s*100", text)
            if m2:
                return float(m2.group(1))
        except Exception:
            pass
        return None

    def _model_response_to_dict(
        self, response_obj, filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert a ModelResponse-like object to results dict"""
        # response_obj may be a dataclass or dict; handle both
        content = getattr(response_obj, "content", None) or (
            response_obj.get("content") if isinstance(response_obj, dict) else ""
        )
        metadata = getattr(response_obj, "metadata", None) or (
            response_obj.get("metadata") if isinstance(response_obj, dict) else {}
        )
        provider = getattr(response_obj, "provider", None) or (
            response_obj.get("provider") if isinstance(response_obj, dict) else None
        )
        model_name = getattr(response_obj, "model_name", None) or (
            response_obj.get("model_name") if isinstance(response_obj, dict) else None
        )

        # Convert provider enum to string for JSON serialization
        if provider is not None:
            provider = str(provider)

        # try to get score from metadata or parse from content
        score = None
        try:
            if isinstance(metadata, dict) and "score" in metadata:
                score = float(metadata.get("score"))
        except Exception:
            score = None
        if score is None:
            score = self._parse_score_from_text(content or "")

        result = {
            "filename": filename or metadata.get("filename")
            if isinstance(metadata, dict)
            else filename,
            "content": content,
            "provider": provider,
            "model": model_name,
            "score": score if score is not None else 0,
            "metadata": metadata,
        }
        return result

    def batch_analyze(
        self, file_paths: List[str], batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Analyze multiple files in batch"""
        # For standalone mode, try local LLM first, then fallback to heuristic
        if self.mode == "standalone":
            # Try local LLM adapter first
            if hasattr(self, "adapter_engine") and self.adapter_engine:
                try:
                    # Analyze files using local LLM
                    async def analyze_batch():
                        try:
                            if not getattr(self.adapter_engine, "_initialized", False):
                                await self.adapter_engine.initialize()

                            results = []
                            for file_path in file_paths:
                                try:
                                    with open(
                                        file_path,
                                        "r",
                                        encoding="utf-8",
                                        errors="ignore",
                                    ) as f:
                                        content = f.read()

                                    result_obj = await self.adapter_engine.generate(
                                        content,
                                        context={
                                            "filename": file_path,
                                            "mode": self.mode,
                                        },
                                    )
                                    result = self._model_response_to_dict(
                                        result_obj, filename=file_path
                                    )
                                    results.append(result)
                                except Exception as e:
                                    results.append(
                                        {
                                            "error": f"Local LLM analysis failed for {file_path}: {str(e)}",
                                            "file_path": file_path,
                                            "score": 0,
                                        }
                                    )
                            return results
                        finally:
                            # Ensure proper cleanup of adapter resources
                            await self.adapter_engine.cleanup()

                    return asyncio.run(analyze_batch())
                except Exception as e:
                    self.logger.debug(f"Local LLM batch analysis failed: {e}")
                    # Fall back to heuristic analyzer

            # Use heuristic analyzer as fallback
            results = []
            for file_path in file_paths:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    result = self.standalone_checker.analyze_content(
                        content, filename=file_path
                    )
                    results.append(result)
                except Exception as e:
                    results.append(
                        {
                            "error": f"Standalone analysis failed: {str(e)}",
                            "file_path": file_path,
                            "score": 0,
                        }
                    )
            return results

        documents = []

        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                documents.append(
                    {
                        "content": content,
                        "filename": os.path.basename(file_path),
                        "analysis_type": "quality_score",
                    }
                )
            except Exception as e:
                documents.append(
                    {
                        "content": "",
                        "filename": os.path.basename(file_path),
                        "error": f"Failed to read file: {str(e)}",
                    }
                )

        if not documents:
            return []

        # If we have an adapter engine available, use it to analyze documents locally/concurrently
        if self.mode == "phi_only" and not self.adapter_engine:
            # Return errors for all files
            return [
                {
                    "error": "Phi adapter not available",
                    "file_path": fp,
                    "filename": os.path.basename(fp),
                    "score": 0,
                }
                for fp in file_paths
            ]

        if self.adapter_engine and self.mode in ("phi_only", "dual"):

            async def _run_batch():
                try:
                    # Initialize adapter if not already initialized
                    if not getattr(self.adapter_engine, "_initialized", False):
                        await self.adapter_engine.initialize()

                    tasks = []
                    for doc in documents:
                        tasks.append(
                            self.adapter_engine.generate(
                                doc["content"],
                                context={
                                    "filename": doc["filename"],
                                    "mode": self.mode,
                                },
                            )
                        )
                    results_objs = await asyncio.gather(*tasks, return_exceptions=True)
                    results = []
                    for i, res in enumerate(results_objs):
                        if isinstance(res, Exception):
                            results.append(
                                {
                                    "error": str(res),
                                    "file_path": file_paths[i],
                                    "filename": os.path.basename(file_paths[i]),
                                    "score": 0,
                                }
                            )
                        else:
                            results.append(
                                self._model_response_to_dict(
                                    res, filename=os.path.basename(file_paths[i])
                                )
                            )
                    return results
                finally:
                    # Ensure proper cleanup of adapter resources
                    await self.adapter_engine.cleanup()

            return asyncio.run(_run_batch())

        payload = {
            "documents": documents,
            "batch_size": batch_size,
            "analysis_type": "quality_score",
        }

        try:
            response = self.http_client.make_request(
                "POST", "/analyze/batch", json=payload, timeout=60
            )
            if response.status_code == 200:
                batch_result = response.json()
                results = batch_result.get("results", [])

                # Add file paths back to results
                for i, result in enumerate(results):
                    if i < len(file_paths):
                        result["file_path"] = file_paths[i]

                return results
            else:
                # Fall back to individual file analysis with proper async handling
                async def analyze_files_batch():
                    try:
                        # Initialize adapter once for all files
                        if self.adapter_engine and self.mode in ("phi_only", "dual"):
                            if not getattr(self.adapter_engine, "_initialized", False):
                                await self.adapter_engine.initialize()

                        results = []
                        for file_path in file_paths:
                            # Use the same logic as analyze_file but in the same async context
                            abs_file_path = os.path.abspath(
                                os.path.join(
                                    os.path.dirname(__file__), "..", "..", file_path
                                )
                            )

                            if self.adapter_engine and self.mode in (
                                "phi_only",
                                "dual",
                            ):
                                try:
                                    with open(
                                        abs_file_path,
                                        "r",
                                        encoding="utf-8",
                                        errors="ignore",
                                    ) as f:
                                        content = f.read()

                                    result_obj = await self.adapter_engine.generate(
                                        content,
                                        context={
                                            "filename": file_path,
                                            "mode": self.mode,
                                        },
                                    )
                                    result = self._model_response_to_dict(
                                        result_obj, filename=file_path
                                    )
                                    results.append(result)
                                except Exception as e:
                                    self.logger.debug(
                                        f"Adapter analysis failed for {file_path}: {e}"
                                    )
                                    results.append(
                                        {
                                            "error": f"Adapter error: {str(e)}",
                                            "file_path": file_path,
                                            "score": 0,
                                        }
                                    )
                            else:
                                # Fall back to API call
                                payload = {
                                    "file_path": abs_file_path,
                                    "analysis_type": "quality_score",
                                }
                                try:
                                    response = self.http_client.make_request(
                                        "POST",
                                        "/analyze/file",
                                        json=payload,
                                        timeout=15,
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        result["file_path"] = file_path
                                        results.append(result)
                                    else:
                                        results.append(
                                            {
                                                "error": f"API error: {response.status_code}",
                                                "file_path": file_path,
                                                "score": 0,
                                            }
                                        )
                                except Exception as e:
                                    results.append(
                                        {
                                            "error": f"Request failed: {str(e)}",
                                            "file_path": file_path,
                                            "score": 0,
                                        }
                                    )

                        return results
                    finally:
                        # Cleanup adapter
                        if self.adapter_engine and self.mode in ("phi_only", "dual"):
                            await self.adapter_engine.cleanup()

                return asyncio.run(analyze_files_batch())
        except Exception as e:
            self.logger.debug(f"Batch analysis failed: {e}")

            # Fall back to individual file analysis with proper async handling
            async def analyze_files_batch():
                try:
                    # Initialize adapter once for all files
                    if self.adapter_engine and self.mode in ("phi_only", "dual"):
                        if not getattr(self.adapter_engine, "_initialized", False):
                            await self.adapter_engine.initialize()

                    results = []
                    for file_path in file_paths:
                        # Use the same logic as analyze_file but in the same async context
                        abs_file_path = os.path.abspath(
                            os.path.join(
                                os.path.dirname(__file__), "..", "..", file_path
                            )
                        )

                        if self.adapter_engine and self.mode in ("phi_only", "dual"):
                            try:
                                with open(
                                    abs_file_path,
                                    "r",
                                    encoding="utf-8",
                                    errors="ignore",
                                ) as f:
                                    content = f.read()

                                result_obj = await self.adapter_engine.generate(
                                    content,
                                    context={"filename": file_path, "mode": self.mode},
                                )
                                result = self._model_response_to_dict(
                                    result_obj, filename=file_path
                                )
                                results.append(result)
                            except Exception as e:
                                self.logger.debug(
                                    f"Adapter analysis failed for {file_path}: {e}"
                                )
                                results.append(
                                    {
                                        "error": f"Adapter error: {str(e)}",
                                        "file_path": file_path,
                                        "score": 0,
                                    }
                                )
                        else:
                            # Fall back to API call
                            payload = {
                                "file_path": abs_file_path,
                                "analysis_type": "quality_score",
                            }
                            try:
                                response = self.http_client.make_request(
                                    "POST", "/analyze/file", json=payload, timeout=15
                                )
                                if response.status_code == 200:
                                    result = response.json()
                                    result["file_path"] = file_path
                                    results.append(result)
                                else:
                                    results.append(
                                        {
                                            "error": f"API error: {response.status_code}",
                                            "file_path": file_path,
                                            "score": 0,
                                        }
                                    )
                            except Exception as e:
                                results.append(
                                    {
                                        "error": f"Request failed: {str(e)}",
                                        "file_path": file_path,
                                        "score": 0,
                                    }
                                )

                    return results
                finally:
                    # Cleanup adapter
                    if self.adapter_engine and self.mode in ("phi_only", "dual"):
                        await self.adapter_engine.cleanup()

            return asyncio.run(analyze_files_batch())
