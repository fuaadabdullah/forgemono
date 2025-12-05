import logging
import os
from functools import wraps
from typing import Callable


class DebugLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.enabled = os.getenv("DEBUG_AUTH", "false").lower() == "true"

    def log_import(self, module_name: str):
        """Log module imports"""
        if self.enabled:
            self.logger.debug(f"📦 Importing {module_name}")

    def log_route_registration(self, router_name: str, routes: list):
        """Log route registration"""
        if self.enabled:
            self.logger.debug(f"🛣️  Registering {router_name} routes:")
            for route in routes:
                try:
                    methods = getattr(route, "methods", None)
                    path = getattr(route, "path", None)
                    name = getattr(route, "name", None)
                    self.logger.debug(f"   {methods} {path} -> {name}")
                except Exception:
                    self.logger.debug(f"   (unable to introspect route {route})")

    def trace_function(self, func: Callable):
        """Decorator to trace async function calls"""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.enabled:
                self.logger.debug(f"→ Calling {func.__name__} with {len(args)} args")
            try:
                result = await func(*args, **kwargs)
                if self.enabled:
                    self.logger.debug(f"← {func.__name__} completed successfully")
                return result
            except Exception as e:
                if self.enabled:
                    self.logger.debug(f"✗ {func.__name__} failed: {e}")
                raise

        return wrapper
