"""
Adapter Manager for Local LLM Integration

This module contains the AdapterManager class that handles initialization
and management of local LLM adapters for the documentation quality checker.
"""

import logging
import os
import sys
from typing import Optional

import yaml


class AdapterManager:
    """Manager for local LLM adapters"""

    def __init__(
        self,
        mode: Optional[str] = None,
        config_file: Optional[str] = None,
        soft_fallback: Optional[bool] = False,
        api_url: str = "https://thomasena-auxochromic-joziah.ngrok-free.dev",
    ):
        self.mode = mode
        self.config_file = config_file
        self.soft_fallback = soft_fallback
        self.api_url = api_url
        self.adapter_engine = None
        self.logger = logging.getLogger(__name__)

    def init_adapter_engine(self):
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
        soft_fallback_val = self.soft_fallback or soft_fallback_cfg
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

    def get_adapter_engine(self):
        """Get the current adapter engine"""
        return self.adapter_engine
