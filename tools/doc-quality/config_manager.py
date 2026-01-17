"""
Configuration Manager Module for Documentation Quality Checker
Handles configuration file loading, validation, and environment variable management
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None


class ConfigManager:
    """Manages configuration for the documentation quality checker"""

    def __init__(
        self, config_file: Optional[str] = None, search_paths: Optional[list] = None
    ):
        if search_paths is None:
            search_paths = [
                ".",
                os.path.dirname(__file__),
                os.path.join(os.path.dirname(__file__), "..", ".."),
            ]
        self.search_paths = search_paths
        self.config_file = config_file
        self._config_cache = None

    def load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or search for default config"""
        if self._config_cache is not None:
            return self._config_cache

        config_file = config_file or self.config_file or self._find_config_file()

        if config_file and os.path.exists(config_file):
            if not YAML_AVAILABLE:
                print(f"Warning: YAML library not available, using default config")
                return self._get_default_config()
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                self._config_cache = config
                return config
            except Exception as e:
                print(f"Warning: Failed to load config file {config_file}: {e}")
                return self._get_default_config()
        else:
            return self._get_default_config()

    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in search paths"""
        config_names = [
            "doc_quality_config.yaml",
            "doc_quality_config.yml",
            ".doc_quality.yaml",
            ".doc_quality.yml",
        ]

        for path in self.search_paths:
            for name in config_names:
                config_path = os.path.join(path, name)
                if os.path.exists(config_path):
                    return config_path

        return None

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "models": {
                "phi3": {
                    "model_name": "microsoft/Phi-3-mini-4k-instruct",
                    "url": "http://localhost:11434",
                    "timeout": 5,
                    "soft_fallback": False,
                },
                "raptor": {
                    "model_name": "raptor-mini",
                    "url": "https://thomasena-auxochromic-joziah.ngrok-free.dev",
                    "timeout": 20,
                },
            },
            "thresholds": {
                "auto_polish": 70.0,
                "min_score": 60,
                "warning_score": 80,
            },
            "file_discovery": {
                "extensions": [".md", ".txt", ".rst", ".adoc"],
                "recursive": True,
                "min_size": None,
                "max_size": None,
            },
            "reporting": {
                "output_formats": ["json", "markdown", "text"],
                "include_metadata": True,
                "show_improvements": True,
            },
        }

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model"""
        config = self.load_config()
        models = config.get("models", {})
        return models.get(model_name, {})

    def get_thresholds(self) -> Dict[str, Any]:
        """Get quality thresholds"""
        config = self.load_config()
        return config.get("thresholds", {})

    def get_file_discovery_config(self) -> Dict[str, Any]:
        """Get file discovery configuration"""
        config = self.load_config()
        return config.get("file_discovery", {})

    def get_reporting_config(self) -> Dict[str, Any]:
        """Get reporting configuration"""
        config = self.load_config()
        return config.get("reporting", {})

    def merge_with_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration with environment variables"""
        merged = config.copy()

        # Environment variable mappings
        env_mappings = {
            "RAPTOR_API_URL": ["models", "raptor", "url"],
            "PHI_MODEL_URL": ["models", "phi3", "url"],
            "DOC_QUALITY_MIN_SCORE": ["thresholds", "min_score"],
            "DOC_QUALITY_WARNING_SCORE": ["thresholds", "warning_score"],
            "DOC_QUALITY_AUTO_POLISH": ["thresholds", "auto_polish"],
        }

        for env_var, config_path in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                self._set_nested_value(
                    merged, config_path, self._parse_env_value(env_value)
                )

        return merged

    def _set_nested_value(self, config: Dict[str, Any], path: list, value: Any):
        """Set a value in a nested dictionary using a path list"""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    def _parse_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Parse environment variable value to appropriate type"""
        # Try boolean
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Try int
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def validate_config(self, config: Dict[str, Any]) -> list:
        """Validate configuration and return list of errors"""
        errors = []

        # Validate models section
        models = config.get("models", {})
        if not isinstance(models, dict):
            errors.append("models section must be a dictionary")
        else:
            for model_name, model_config in models.items():
                if not isinstance(model_config, dict):
                    errors.append(f"model {model_name} config must be a dictionary")
                    continue

                required_fields = ["url", "timeout"]
                for field in required_fields:
                    if field not in model_config:
                        errors.append(
                            f"model {model_name} missing required field: {field}"
                        )

        # Validate thresholds section
        thresholds = config.get("thresholds", {})
        if not isinstance(thresholds, dict):
            errors.append("thresholds section must be a dictionary")
        else:
            score_fields = ["min_score", "warning_score", "auto_polish"]
            for field in score_fields:
                if field in thresholds:
                    value = thresholds[field]
                    if not isinstance(value, (int, float)):
                        errors.append(f"threshold {field} must be a number")
                    elif not (0 <= value <= 100):
                        errors.append(f"threshold {field} must be between 0 and 100")

        # Validate file_discovery section
        file_discovery = config.get("file_discovery", {})
        if not isinstance(file_discovery, dict):
            errors.append("file_discovery section must be a dictionary")
        else:
            if "extensions" in file_discovery:
                extensions = file_discovery["extensions"]
                if not isinstance(extensions, list):
                    errors.append("file_discovery.extensions must be a list")
                else:
                    for ext in extensions:
                        if not isinstance(ext, str) or not ext.startswith("."):
                            errors.append(
                                f"file_discovery extension {ext} must be a string starting with '.'"
                            )

        return errors

    def save_config(self, config: Dict[str, Any], file_path: str):
        """Save configuration to file"""
        if not YAML_AVAILABLE:
            raise ImportError("YAML library not available - cannot save config")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def get_effective_config(self) -> Dict[str, Any]:
        """Get the effective configuration (file + environment variables)"""
        config = self.load_config()
        return self.merge_with_env(config)

    def reload_config(self):
        """Force reload configuration from file"""
        self._config_cache = None
