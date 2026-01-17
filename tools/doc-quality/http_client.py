"""
HTTP Client for API Communication

This module contains the HTTPClient class that handles API requests,
health checks, and response debugging for the documentation quality checker.
"""

import json
import logging
import os
import time
from typing import Optional

import requests


class HTTPClient:
    """HTTP client for API communication with debugging support"""

    def __init__(
        self,
        api_url: str = "https://thomasena-auxochromic-joziah.ngrok-free.dev",
        debug_api: bool = False,
        debug_timing: bool = False,
        save_responses_dir: Optional[str] = None,
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

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
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

    def check_api_health(self) -> bool:
        """Check if Raptor Mini API is accessible"""
        try:
            response = self.make_request("GET", "/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
