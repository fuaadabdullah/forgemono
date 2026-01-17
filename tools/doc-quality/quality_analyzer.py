"""
Quality Analyzer Module for Documentation Quality Checker
Contains core analysis logic, standalone checker, and model response parsing
"""

import asyncio
import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None


class AnalysisResult:
    """Represents the result of a quality analysis"""

    def __init__(
        self,
        filename: str = "",
        content: str = "",
        provider: str = "",
        model: str = "",
        score: float = 0,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        self.filename = filename
        self.content = content
        self.provider = provider
        self.model = model
        self.score = score
        self.metadata = metadata or {}
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            "filename": self.filename,
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "score": self.score,
            "metadata": self.metadata,
        }
        if self.error:
            result["error"] = self.error
        return result


class QualityAnalyzer(ABC):
    """Abstract base class for quality analyzers"""

    @abstractmethod
    async def analyze_content(
        self, content: str, filename: str = "content.md"
    ) -> AnalysisResult:
        """Analyze content and return results"""
        pass

    @abstractmethod
    async def analyze_file(self, file_path: str) -> AnalysisResult:
        """Analyze a file and return results"""
        pass


class StandaloneQualityAnalyzer(QualityAnalyzer):
    """Standalone quality analyzer that doesn't require external APIs"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def analyze_content(
        self, content: str, filename: str = "content.md"
    ) -> AnalysisResult:
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

            metadata = {
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
            }

            return AnalysisResult(
                filename=filename,
                content=f"Quality Score: {score}/100\nStrength: {strength}\nWeakness: {weakness}",
                provider="standalone",
                model="heuristic_analyzer",
                score=score,
                metadata=metadata,
            )

        except Exception as e:
            return AnalysisResult(
                filename=filename,
                error=f"Standalone analysis failed: {str(e)}",
                score=0,
            )

    async def analyze_file(self, file_path: str) -> AnalysisResult:
        """Analyze a file using standalone heuristics"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return await self.analyze_content(
                content, filename=os.path.basename(file_path)
            )
        except Exception as e:
            return AnalysisResult(
                filename=os.path.basename(file_path),
                error=f"File analysis failed: {str(e)}",
                score=0,
            )


class ModelResponseParser:
    """Parses responses from various models into standardized format"""

    @staticmethod
    def parse_response(response_obj, filename: Optional[str] = None) -> AnalysisResult:
        """Convert a ModelResponse-like object to AnalysisResult"""
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

        # Try to get score from metadata or parse from content
        score = None
        try:
            if isinstance(metadata, dict) and "score" in metadata:
                score = float(metadata.get("score"))
        except Exception:
            score = None
        if score is None:
            score = ModelResponseParser._parse_score_from_text(content or "")

        return AnalysisResult(
            filename=filename or metadata.get("filename")
            if isinstance(metadata, dict)
            else filename,
            content=content,
            provider=provider,
            model=model_name,
            score=score if score is not None else 0,
            metadata=metadata,
        )

    @staticmethod
    def _parse_score_from_text(text: str) -> Optional[float]:
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


class AdapterEngine:
    """Manages local model adapters for quality analysis"""

    def __init__(self, config_file: Optional[str] = None, soft_fallback: bool = False):
        self.config_file = config_file
        self.soft_fallback = soft_fallback
        self.adapter_engine = None
        self.logger = logging.getLogger(__name__)

    def initialize(self):
        """Initialize the adapter engine if available"""
        try:
            self._init_adapter_engine()
        except Exception as e:
            self.logger.debug(f"Adapter engine initialization failed: {e}")

    def _init_adapter_engine(self):
        """Initialize dual/local adapters based on config and mode"""
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
        cfg_path = self.config_file or os.path.join(
            os.path.dirname(__file__), "doc_quality_config.yaml"
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
        )

        raptor_model_config = ModelConfig(
            provider=ModelProvider.RAPTOR_API,
            model_name=raptor_cfg.get("model_name", "raptor-mini"),
            base_url=raptor_cfg.get(
                "url", "https://thomasena-auxochromic-joziah.ngrok-free.dev"
            ),
            timeout=raptor_cfg.get("timeout", 20),
        )

        phi_adapter = LocalModelAdapter(phi_model_config)
        raptor_adapter = RaptorApiAdapter(raptor_model_config)

        # Create DualModelAdapter
        thresholds = config_data.get("thresholds", {})
        auto_polish = float(thresholds.get("auto_polish", 70.0))
        model_cfg = ModelConfig(provider=ModelProvider.FALLBACK, model_name="dual")
        dual_adapter = DualModelAdapter(
            model_cfg,
            phi_adapter,
            raptor_adapter,
            auto_polish_threshold=auto_polish,
            soft_fallback=self.soft_fallback,
        )
        # Don't initialize synchronously - will happen lazily in analyze_content
        self.adapter_engine = dual_adapter

    async def analyze_content(
        self, content: str, filename: str = "content.md", mode: str = "dual"
    ) -> AnalysisResult:
        """Analyze content using the adapter engine"""
        if not self.adapter_engine:
            return AnalysisResult(
                filename=filename, error="Adapter engine not available", score=0
            )

        try:
            # Initialize adapter if not already initialized
            if not getattr(self.adapter_engine, "_initialized", False):
                await self.adapter_engine.initialize()

            result_obj = await self.adapter_engine.generate(
                content, context={"filename": filename, "mode": mode}
            )

            return ModelResponseParser.parse_response(result_obj, filename=filename)

        except Exception as e:
            self.logger.debug(f"Adapter analysis failed: {e}")
            return AnalysisResult(
                filename=filename, error=f"Adapter analysis failed: {str(e)}", score=0
            )
        finally:
            # Ensure proper cleanup of adapter resources
            if self.adapter_engine:
                await self.adapter_engine.cleanup()

    async def analyze_file(self, file_path: str, mode: str = "dual") -> AnalysisResult:
        """Analyze a file using the adapter engine"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            return await self.analyze_content(
                content, filename=os.path.basename(file_path), mode=mode
            )
        except Exception as e:
            return AnalysisResult(
                filename=os.path.basename(file_path),
                error=f"File analysis failed: {str(e)}",
                score=0,
            )

    async def analyze_batch(
        self, file_paths: List[str], mode: str = "dual"
    ) -> List[AnalysisResult]:
        """Analyze multiple files using the adapter engine"""
        if not self.adapter_engine:
            return [
                AnalysisResult(
                    filename=os.path.basename(fp),
                    error="Adapter engine not available",
                    score=0,
                )
                for fp in file_paths
            ]

        try:
            # Initialize adapter if not already initialized
            if not getattr(self.adapter_engine, "_initialized", False):
                await self.adapter_engine.initialize()

            results = []
            for file_path in file_paths:
                try:
                    result = await self.analyze_file(file_path, mode)
                    results.append(result)
                except Exception as e:
                    results.append(
                        AnalysisResult(
                            filename=os.path.basename(file_path),
                            error=f"Batch analysis failed: {str(e)}",
                            score=0,
                        )
                    )

            return results

        except Exception as e:
            self.logger.debug(f"Batch adapter analysis failed: {e}")
            return [
                AnalysisResult(
                    filename=os.path.basename(fp),
                    error=f"Batch analysis failed: {str(e)}",
                    score=0,
                )
                for fp in file_paths
            ]
        finally:
            # Ensure proper cleanup of adapter resources
            if self.adapter_engine:
                await self.adapter_engine.cleanup()
