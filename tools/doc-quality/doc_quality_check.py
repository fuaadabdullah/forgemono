#!/usr/bin/env python3
"""
Documentation Quality Check CLI Tool
Automated quality analysis for ForgeMonorepo documentation using Raptor Mini API

Usage:
    python doc_quality_check.py [options] [files...]

Examples:
    # Check all documentation files
    python doc_quality_check.py

    # Check specific files
    python doc_quality_check.py docs/README.md docs/WORKSPACE_OVERVIEW.md

    # Check with custom thresholds
    python doc_quality_check.py --min-score 80 --fail-on-warnings

    # Generate detailed report
    python doc_quality_check.py --report doc_quality_report.json

    # CI mode (non-interactive, exit codes)
    python doc_quality_check.py --ci --min-score 70

    # Debug mode with verbose logging
    python doc_quality_check.py --debug --debug-api --debug-timing

    # Save API responses for debugging
    python doc_quality_check.py --save-responses ./debug_responses

    # STANDALONE MODE - No external dependencies required
    python doc_quality_check.py --standalone
    python doc_quality_check.py docs/*.md --standalone --json
"""

import argparse
import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import yaml
import asyncio

importlib = None


class StandaloneQualityChecker:
    """Standalone quality checker that doesn't require external APIs"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_content(
        self, content: str, filename: str = "content.md"
    ) -> Dict[str, Any]:
        """Analyze content using simple heuristics"""
        try:
            # Basic metrics
            lines = content.split("\n")
            sentences = [
                s.strip() for s in content.replace("\n", " ").split(".") if s.strip()
            ]
            words = content.split()
            chars = len(content)

            # Calculate score based on heuristics
            score = 50  # Base score

            # Length bonuses
            if chars > 1000:
                score += 15
            elif chars > 500:
                score += 10
            elif chars > 200:
                score += 5

            # Structure bonuses
            if "#" in content:  # Has headers
                score += 10
            if "`" in content:  # Has code examples
                score += 10
            if "- " in content or "* " in content:  # Has lists
                score += 5

            # Content quality bonuses
            if len(sentences) > 10:
                score += 10
            if len(words) > 100:
                score += 5

            # Readability check (simple)
            avg_words_per_sentence = len(words) / max(len(sentences), 1)
            if 10 <= avg_words_per_sentence <= 25:
                score += 5

            # Cap at 100
            score = min(score, 100)

            # Determine strength/weakness
            if score >= 80:
                strength = "Good structure and content depth"
                weakness = "Could benefit from more specific examples"
                improvements = []
            elif score >= 60:
                strength = "Basic structure present"
                weakness = "Needs more detailed content and examples"
                improvements = [
                    "Add section headers",
                    "Include code examples",
                    "Expand explanations",
                ]
            else:
                strength = "Minimal content"
                weakness = "Significant improvements needed"
                improvements = [
                    "Add comprehensive content",
                    "Include examples",
                    "Improve structure",
                ]

            return {
                "filename": filename,
                "content": f"Quality Score: {score}/100\nStrength: {strength}\nWeakness: {weakness}",
                "provider": "standalone",
                "model": "heuristic_analyzer",
                "score": score,
                "metadata": {
                    "analysis_type": "quality_score",
                    "content_length": chars,
                    "sentence_count": len(sentences),
                    "word_count": len(words),
                    "line_count": len(lines),
                    "raw_response": {
                        "score": score,
                        "strength": strength,
                        "weakness": weakness,
                        "improvements": improvements,
                    },
                },
            }

        except Exception as e:
            return {
                "error": f"Standalone analysis failed: {str(e)}",
                "filename": filename,
                "score": 0,
            }


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
        self.api_url = api_url
        self.debug_api = debug_api
        self.debug_timing = debug_timing
        self.save_responses_dir = save_responses_dir
        self.session = requests.Session()
        self.request_count = 0

        # Set up debug logging
        if debug_api or debug_timing:
            logging.basicConfig(
                level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
            )
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.WARNING)

        # Create save responses directory if specified
        if self.save_responses_dir:
            os.makedirs(self.save_responses_dir, exist_ok=True)

        self._check_api_health()

        # If mode provided, initialize adapters
        self.mode = mode or os.environ.get("RAPTOR_MODE", "dual")
        if self.mode == "standalone":
            # For standalone mode, try to initialize local LLM adapters
            self.logger.debug("Running in standalone mode - initializing local LLMs")
            self.config_file = config_file
            self.soft_fallback = soft_fallback or os.environ.get(
                "DOC_QUALITY_SOFT_FALLBACK", "false"
            ).lower() in (
                "true",
                "1",
                "yes",
            )
            self.adapter_engine = None
            try:
                self._init_adapter_engine()
            except Exception as e:
                # Non-fatal: adapter may not be available, will use heuristic fallback
                self.logger.debug(f"Local LLM initialization failed: {e}")
        else:
            self._check_api_health()
            self.config_file = config_file
            self.soft_fallback = soft_fallback or os.environ.get(
                "DOC_QUALITY_SOFT_FALLBACK", "false"
            ).lower() in (
                "true",
                "1",
                "yes",
            )
            self.adapter_engine = None
            try:
                self._init_adapter_engine()
            except Exception as e:
                # Non-fatal: adapter may not be available
                self.logger.debug(f"Adapter engine initialization failed: {e}")

        # Initialize standalone checker as final fallback
        self.standalone_checker = StandaloneQualityChecker()

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make API request with debugging support"""
        url = f"{self.api_url}{endpoint}"
        self.request_count += 1

        if self.debug_api:
            self.logger.debug(f"API Request #{self.request_count}: {method} {url}")
            if "json" in kwargs:
                self.logger.debug(
                    f"Request payload: {json.dumps(kwargs['json'], indent=2)}"
                )

        start_time = time.time()
        try:
            response = self.session.request(method, url, **kwargs)
            elapsed = time.time() - start_time

            if self.debug_api:
                self.logger.debug(f"Response status: {response.status_code}")
                self.logger.debug(f"Response time: {elapsed:.3f}s")
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    try:
                        response_json = response.json()
                        self.logger.debug(
                            f"Response body: {json.dumps(response_json, indent=2)}"
                        )
                    except Exception as e:
                        self.logger.debug(
                            f"Response body (text): {response.text[:500]}... (JSON parse error: {e})"
                        )

            if self.debug_timing:
                self.logger.info(f"API call to {endpoint} took {elapsed:.3f}s")

            # Save response if requested
            if self.save_responses_dir:
                timestamp = int(time.time())
                filename = f"response_{self.request_count}_{timestamp}.json"
                filepath = os.path.join(self.save_responses_dir, filename)

                response_data = {
                    "request": {
                        "method": method,
                        "url": url,
                        "payload": kwargs.get("json", {}),
                        "timestamp": timestamp,
                    },
                    "response": {
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "elapsed": elapsed,
                        "content": response.text,
                    },
                }

                try:
                    with open(filepath, "w") as f:
                        json.dump(response_data, f, indent=2)
                    self.logger.debug(f"Saved response to: {filepath}")
                except Exception as e:
                    self.logger.warning(f"Failed to save response: {e}")

            return response

        except Exception as e:
            elapsed = time.time() - start_time
            if self.debug_api:
                self.logger.error(f"Request failed after {elapsed:.3f}s: {e}")
            raise

    def _check_api_health(self) -> bool:
        """Check if Raptor Mini API is accessible"""
        try:
            response = self._make_request("GET", "/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single file"""
        # For standalone mode, try local LLM first, then fallback to heuristic
        if self.mode == "standalone":
            # Try local LLM adapter first
            if hasattr(self, "adapter_engine") and self.adapter_engine:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Initialize and generate in the same event loop
                    async def init_and_generate():
                        try:
                            if not getattr(self.adapter_engine, "_initialized", False):
                                await self.adapter_engine.initialize()
                            return await self.adapter_engine.generate(
                                content,
                                context={"filename": file_path, "mode": self.mode},
                            )
                        finally:
                            # Ensure proper cleanup of adapter resources
                            await self.adapter_engine.cleanup()

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
            response = self._make_request(
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
            response = self._make_request("POST", "/analyze", json=payload, timeout=15)
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

    def _init_adapter_engine(self):
        """Initialize dual/local adapters based on config and mode
        This method will import the adapters from the raptor-mini package and create an engine.
        """
        # Only initialize if running in phi_only, dual, or standalone modes
        if self.mode not in ("phi_only", "dual", "standalone"):
            return

        # Add the raptor-mini directory to sys.path for imports
        raptor_mini_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "raptor-mini")
        )
        if raptor_mini_dir not in sys.path:
            sys.path.insert(0, raptor_mini_dir)

        # Import adapters (optional for standalone mode)
        try:
            from raptor_adapter import (
                LocalModelAdapter,
                RaptorApiAdapter,
                DualModelAdapter,
                ModelConfig,
                ModelProvider,
            )

            adapters_available = True
        except ImportError:
            self.logger.debug(
                "Raptor adapter not available, running in standalone mode"
            )
            adapters_available = False

        if not adapters_available:
            return

        # Load config file if present
        cfg_path = self.config_file or os.environ.get(
            "DOC_QUALITY_CONFIG", "tools/doc-quality/doc_quality_config.yaml"
        )
        config_data = {}
        try:
            with open(cfg_path, "r") as f:
                config_data = yaml.safe_load(f)
        except Exception:
            config_data = {}

        models_cfg = config_data.get("models", {})
        phi_cfg = models_cfg.get("phi3", {})
        raptor_cfg = models_cfg.get("raptor", {})

        # Build ModelConfig objects
        phi_model_config = ModelConfig(
            provider=ModelProvider.LOCAL_LLAMA,
            model_name=phi_cfg.get("model_name") or phi_cfg.get("url"),
            base_url=phi_cfg.get("url"),
            timeout=phi_cfg.get("timeout", 5),
            # capabilities left to default
        )

        raptor_model_config = ModelConfig(
            provider=ModelProvider.RAPTOR_API,
            model_name=raptor_cfg.get("model_name", "raptor-mini"),
            base_url=raptor_cfg.get("url", self.api_url),
            timeout=raptor_cfg.get("timeout", 20),
            # capabilities left to default
        )

        phi_adapter = LocalModelAdapter(phi_model_config)
        raptor_adapter = RaptorApiAdapter(raptor_model_config)

        # Create DualModelAdapter
        thresholds = config_data.get("thresholds", {})
        auto_polish = float(thresholds.get("auto_polish", 70.0))
        model_cfg = ModelConfig(provider=ModelProvider.FALLBACK, model_name="dual")
        soft_fallback_cfg = phi_cfg.get("soft_fallback", False)
        # CLI arg overrides config
        soft_fallback_val = getattr(self, "soft_fallback", False) or soft_fallback_cfg
        dual_adapter = DualModelAdapter(
            model_cfg,
            phi_adapter,
            raptor_adapter,
            auto_polish_threshold=auto_polish,
            soft_fallback=soft_fallback_val,
        )
        # Don't initialize synchronously - will happen lazily in analyze_content
        self.adapter_engine = dual_adapter

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
            response = self._make_request(
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
                                    response = self._make_request(
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
                                response = self._make_request(
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


class QualityReporter:
    """Generate quality reports and summaries"""

    def __init__(self, results: List[Dict[str, Any]]):
        self.results = results
        self.valid_results = [
            r for r in results if "score" in r and isinstance(r["score"], (int, float))
        ]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.valid_results:
            return {
                "total_files": len(self.results),
                "analyzed_files": 0,
                "average_score": 0,
                "min_score": 0,
                "max_score": 0,
                "high_quality": 0,
                "medium_quality": 0,
                "low_quality": 0,
                "errors": len(self.results),
            }

        scores = [r["score"] for r in self.valid_results]

        return {
            "total_files": len(self.results),
            "analyzed_files": len(self.valid_results),
            "average_score": round(sum(scores) / len(scores), 1),
            "min_score": min(scores),
            "max_score": max(scores),
            "high_quality": len([s for s in scores if s >= 80]),
            "medium_quality": len([s for s in scores if 60 <= s < 80]),
            "low_quality": len([s for s in scores if s < 60]),
            "errors": len(self.results) - len(self.valid_results),
        }

    def get_failed_files(self, min_score: int = 70) -> List[Dict[str, Any]]:
        """Get files that failed quality check"""
        return [r for r in self.valid_results if r.get("score", 0) < min_score]

    def get_top_performers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing files"""
        return sorted(self.valid_results, key=lambda x: x["score"], reverse=True)[
            :limit
        ]

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate detailed report"""
        stats = self.get_summary_stats()
        failed_files = self.get_failed_files()
        top_performers = self.get_top_performers()

        report = []
        report.append("# Documentation Quality Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        report.append("## Summary Statistics")
        report.append(f"- **Total Files**: {stats['total_files']}")
        report.append(f"- **Successfully Analyzed**: {stats['analyzed_files']}")
        report.append(f"- **Average Score**: {stats['average_score']}/100")
        report.append(f"- **Score Range**: {stats['min_score']} - {stats['max_score']}")
        report.append(f"- **High Quality (≥80)**: {stats['high_quality']}")
        report.append(f"- **Medium Quality (60-79)**: {stats['medium_quality']}")
        report.append(f"- **Low Quality (<60)**: {stats['low_quality']}")
        if stats["errors"] > 0:
            report.append(f"- **Errors**: {stats['errors']}")
        report.append("")

        if top_performers:
            report.append("## Top Performing Files")
            for i, result in enumerate(top_performers, 1):
                filename = result.get("filename", result.get("file_path", "unknown"))
                score = result["score"]
                strength = result.get("strength", "unknown")
                report.append(f"{i}. **{filename}**: {score}/100 - {strength}")
            report.append("")

        if failed_files:
            report.append("## Files Needing Improvement")
            for result in failed_files:
                filename = result.get("filename", result.get("file_path", "unknown"))
                score = result["score"]
                weakness = result.get("weakness", "unknown")
                improvements = result.get("improvements", [])
                report.append(f"- **{filename}** ({score}/100): {weakness}")
                if improvements:
                    report.append(f"  - Suggestions: {', '.join(improvements)}")
            report.append("")

        # Individual file results
        report.append("## Individual File Results")
        for result in self.results:
            filename = result.get("filename", result.get("file_path", "unknown"))

            if "error" in result:
                report.append(f"- **{filename}**: ❌ Error - {result['error']}")
            else:
                score = result.get("score", 0)
                strength = result.get("strength", "unknown")
                report.append(f"- **{filename}**: {score}/100 - {strength}")

        report_text = "\n".join(report)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_text)
            print(f"📄 Report saved to: {output_file}")

        return report_text


def find_doc_files(
    directory: str = "docs", extensions: List[str] = None, debug: bool = False
) -> List[str]:
    """Find documentation files in directory"""
    if extensions is None:
        extensions = [".md", ".txt", ".rst", ".adoc"]

    if debug:
        print(f"🐛 Debug: Searching for documentation files in: {directory}")
        print(f"🐛 Debug: File extensions: {', '.join(extensions)}")

    doc_files = []
    docs_path = Path(directory)

    if not docs_path.exists():
        if debug:
            print(f"🐛 Debug: Directory {directory} does not exist")
        return doc_files

    for ext in extensions:
        found_files = list(docs_path.rglob(f"*{ext}"))
        if debug:
            print(f"🐛 Debug: Found {len(found_files)} files with extension {ext}")
        doc_files.extend(str(p) for p in found_files)

    if debug:
        print(f"🐛 Debug: Total files found: {len(doc_files)}")

    return sorted(doc_files)


def main():
    """Main CLI function"""

    # Check environment variables for debug settings
    env_debug = os.getenv("DOC_QUALITY_DEBUG", "").lower() in ("true", "1", "yes")
    env_debug_api = os.getenv("DOC_QUALITY_DEBUG_API", "").lower() in (
        "true",
        "1",
        "yes",
    )
    env_debug_timing = os.getenv("DOC_QUALITY_DEBUG_TIMING", "").lower() in (
        "true",
        "1",
        "yes",
    )
    env_debug_files = os.getenv("DOC_QUALITY_DEBUG_FILES", "").lower() in (
        "true",
        "1",
        "yes",
    )

    parser = argparse.ArgumentParser(
        description="Automated documentation quality checks using Raptor Mini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check all docs in docs/ directory
  python doc_quality_check.py

  # Check specific files
  python doc_quality_check.py docs/README.md docs/WORKSPACE_OVERVIEW.md

  # CI mode with quality gate
  python doc_quality_check.py --ci --min-score 70

  # Generate detailed report
  python doc_quality_check.py --report quality_report.md

  # Check with custom API URL
  python doc_quality_check.py --api-url http://localhost:8000
        """,
    )

    parser.add_argument(
        "files", nargs="*", help="Specific files to check (default: all docs in docs/)"
    )

    parser.add_argument(
        "--api-url",
        default="https://thomasena-auxochromic-joziah.ngrok-free.dev",
        help="Raptor Mini API URL",
    )

    parser.add_argument(
        "--min-score",
        type=int,
        default=60,
        help="Minimum acceptable score (default: 60)",
    )

    parser.add_argument(
        "--report", help="Generate detailed report file (supports .md, .json, .txt)"
    )

    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit with code 1 if quality check fails",
    )

    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Treat scores below 80 as failures",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for processing multiple files",
    )

    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")

    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Run in standalone mode (no external dependencies required)",
    )

    # Debug options
    parser.add_argument(
        "--debug",
        action="store_true",
        default=env_debug,
        help="Enable debug mode with verbose logging",
    )

    parser.add_argument(
        "--debug-api",
        action="store_true",
        default=env_debug_api,
        help="Show detailed API request/response information",
    )

    parser.add_argument(
        "--debug-timing",
        action="store_true",
        default=env_debug_timing,
        help="Show timing information for operations",
    )

    parser.add_argument(
        "--debug-files",
        action="store_true",
        default=env_debug_files,
        help="Show file discovery and processing details",
    )

    parser.add_argument(
        "--save-responses", help="Save raw API responses to specified directory"
    )

    parser.add_argument(
        "--mode",
        default=os.environ.get("RAPTOR_MODE", "dual"),
        choices=["phi_only", "raptor_only", "dual"],
        help="Model orchestration mode: phi_only, raptor_only, or dual",
    )

    parser.add_argument(
        "--config",
        default=os.environ.get(
            "DOC_QUALITY_CONFIG", "tools/doc-quality/doc_quality_config.yaml"
        ),
        help="Path to configuration YAML file",
    )

    parser.add_argument(
        "--soft-fallback",
        action="store_true",
        default=os.environ.get("DOC_QUALITY_SOFT_FALLBACK", "false").lower()
        in ("true", "1", "yes"),
        help="Allow phi_only to soft-fallback to Raptor API if local Phi is down",
    )

    args = parser.parse_args()

    # Initialize checker
    try:
        checker = DocQualityChecker(
            api_url=args.api_url,
            debug_api=args.debug_api,
            debug_timing=args.debug_timing,
            save_responses_dir=args.save_responses,
            mode="standalone" if args.standalone else args.mode,
            config_file=args.config,
            soft_fallback=args.soft_fallback,
        )
    except Exception as e:
        print(f"❌ Failed to initialize quality checker: {e}")
        sys.exit(1)

    # Determine files to check
    if args.files:
        files_to_check = args.files
        if args.debug_files:
            print(f"🐛 Debug: Using {len(files_to_check)} specified files:")
            for f in files_to_check:
                print(f"  • {f}")
    else:
        files_to_check = find_doc_files(debug=args.debug_files)
        if args.debug_files:
            print(
                f"🐛 Debug: Auto-discovered {len(files_to_check)} files in docs/ directory"
            )
            for f in files_to_check[:10]:  # Show first 10
                print(f"  • {f}")
            if len(files_to_check) > 10:
                print(f"  ... and {len(files_to_check) - 10} more")

    if not files_to_check:
        print("❌ No documentation files found to check")
        sys.exit(1)

    if not args.quiet:
        print(f"🔍 Checking {len(files_to_check)} documentation files...")
        print(f"📊 Using API: {args.api_url}")
        print(f"🎯 Minimum score: {args.min_score}")
        print()

    # Analyze files
    analysis_start_time = time.time()
    if len(files_to_check) == 1:
        # Single file analysis
        if args.debug_timing:
            print("🐛 Debug: Starting single file analysis...")
        result = checker.analyze_file(files_to_check[0])
        results = [result]
    else:
        # Batch analysis
        if args.debug_timing:
            print(
                f"🐛 Debug: Starting batch analysis with batch_size={args.batch_size}..."
            )
        results = checker.batch_analyze(files_to_check, args.batch_size)

    analysis_elapsed = time.time() - analysis_start_time

    if args.debug_timing:
        print(f"🐛 Debug: Analysis completed in {analysis_elapsed:.3f}s")
        print(
            f"🐛 Debug: Average time per file: {analysis_elapsed / len(files_to_check):.3f}s"
        )
        print(f"🐛 Debug: Total API requests made: {checker.request_count}")

    if args.debug:
        print("🐛 Debug: Analysis results summary:")
        successful_results = [
            r for r in results if "score" in r and isinstance(r["score"], (int, float))
        ]
        error_results = [r for r in results if "error" in r]
        print(f"  • Total results: {len(results)}")
        print(f"  • Successful analyses: {len(successful_results)}")
        print(f"  • Errors: {len(error_results)}")
        if error_results:
            print("  • Error details:")
            for error_result in error_results[:5]:  # Show first 5 errors
                filename = error_result.get(
                    "filename", error_result.get("file_path", "unknown")
                )
                print(f"    - {filename}: {error_result['error']}")
            if len(error_results) > 5:
                print(f"    ... and {len(error_results) - 5} more errors")

    # Create reporter
    reporter = QualityReporter(results)
    stats = reporter.get_summary_stats()

    # Output results
    if args.json:
        # JSON output for automation
        output = {
            "timestamp": time.time(),
            "api_url": args.api_url,
            "files_checked": len(files_to_check),
            "statistics": stats,
            "results": results,
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        if not args.quiet:
            print("📊 Quality Check Results")
            print("=" * 40)
            print(f"Files analyzed: {stats['analyzed_files']}/{stats['total_files']}")
            print(f"Average score: {stats['average_score']}/100")
            print(f"Score range: {stats['min_score']} - {stats['max_score']}")
            print(f"High quality (≥80): {stats['high_quality']}")
            print(f"Medium quality (60-79): {stats['medium_quality']}")
            print(f"Low quality (<60): {stats['low_quality']}")
            if stats["errors"] > 0:
                print(f"Errors: {stats['errors']}")
            print()

        # Show failed files
        failed_files = reporter.get_failed_files(args.min_score)
        if failed_files:
            if not args.quiet:
                print("❌ Files below minimum score:")
                for result in failed_files:
                    filename = result.get(
                        "filename", result.get("file_path", "unknown")
                    )
                    score = result["score"]
                    weakness = result.get("weakness", "unknown")
                    print(f"  • {filename}: {score}/100 - {weakness}")
                print()

    # Generate report if requested
    if args.report:
        reporter.generate_report(args.report)
        if not args.quiet:
            print(f"📄 Detailed report saved to: {args.report}")

    # Determine exit code for CI
    min_threshold = 80 if args.fail_on_warnings else args.min_score
    failed_files = reporter.get_failed_files(min_threshold)

    if args.ci and failed_files:
        if not args.quiet:
            print(
                f"❌ Quality check failed: {len(failed_files)} files below threshold ({min_threshold})"
            )
        sys.exit(1)
    elif failed_files:
        if not args.quiet:
            print(
                f"⚠️  Warning: {len(failed_files)} files below recommended threshold ({min_threshold})"
            )
    else:
        if not args.quiet:
            print("✅ All files passed quality check!")


if __name__ == "__main__":
    main()
