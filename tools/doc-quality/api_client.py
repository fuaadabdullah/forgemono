"""
API Client Module for Documentation Quality Checker
Handles all communication with external APIs (Raptor Mini, etc.)
"""

import json
import os
import time
from typing import Dict, Any, Optional
import logging
from pathlib import Path

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class APIClient:
    """Handles API communication for documentation quality analysis"""

    def __init__(
        self,
        api_url: str = "https://thomasena-auxochromic-joziah.ngrok-free.dev",
        debug_api: bool = False,
        debug_timing: bool = False,
        save_responses_dir: Optional[str] = None,
        timeout: int = 15,
    ):
        self.api_url = api_url
        self.debug_api = debug_api
        self.debug_timing = debug_timing
        self.save_responses_dir = save_responses_dir
        self.timeout = timeout
        self.requests_available = REQUESTS_AVAILABLE

        if not self.requests_available:
            self.logger = logging.getLogger(__name__)
            self.logger.warning(
                "requests library not available - API functionality disabled"
            )
            self.session = None
            self.request_count = 0
        else:
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
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
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

    def check_health(self) -> bool:
        """Check if the API is accessible"""
        if not self.requests_available:
            return False
        try:
            response = self._make_request("GET", "/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single file via API"""
        if not self.requests_available:
            return {
                "error": "requests library not available",
                "file_path": file_path,
                "score": 0,
            }

        payload = {"file_path": file_path, "analysis_type": "quality_score"}
        try:
            response = self._make_request(
                "POST", "/analyze/file", json=payload, timeout=self.timeout
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

    def analyze_content(
        self, content: str, filename: str = "content.md"
    ) -> Dict[str, Any]:
        """Analyze content directly via API"""
        if not self.requests_available:
            return {
                "error": "requests library not available",
                "filename": filename,
                "score": 0,
            }

        payload = {
            "task": "analyze_document",
            "content": content,
            "analysis_type": "quality_score",
        }

        try:
            response = self._make_request(
                "POST", "/analyze", json=payload, timeout=self.timeout
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

    def analyze_batch(self, documents: list, batch_size: int = 10) -> list:
        """Analyze multiple documents in batch"""
        if not self.requests_available:
            return [
                {
                    "error": "requests library not available",
                    "filename": doc.get("filename", f"doc_{i}"),
                    "score": 0,
                }
                for i, doc in enumerate(documents)
            ]

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
                    if i < len(documents):
                        result["filename"] = documents[i].get("filename", f"doc_{i}")

                return results
            else:
                # Return error results for all documents
                return [
                    {
                        "error": f"Batch API error: {response.status_code}",
                        "filename": doc.get("filename", f"doc_{i}"),
                        "score": 0,
                    }
                    for i, doc in enumerate(documents)
                ]
        except Exception as e:
            return [
                {
                    "error": f"Batch request failed: {str(e)}",
                    "filename": doc.get("filename", f"doc_{i}"),
                    "score": 0,
                }
                for i, doc in enumerate(documents)
            ]
