#!/usr/bin/env python3
"""
Raptor Mini Document Analyzer
"""

import requests
import json
from pathlib import Path
from typing import Dict
import sys


class RaptorAnalyzer:
    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "raptor-mini"
    ):
        self.base_url = base_url
        self.model = model

    def analyze(self, content: str) -> Dict:
        prompt = f"""Analyze this documentation and provide feedback on clarity, completeness, and structure.
        Provide a score from 0-100 and three suggestions for improvement.

        Document content:
        {content[:3000]}  # Limit content to avoid token limits

        Provide feedback in the following JSON format:
        {{
            "score": 85,
            "feedback": ["Good structure", "Clear examples"],
            "suggestions": ["Add more context", "Include a diagram"]
        }}
        """

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 500,
                    },
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                # Try to parse JSON from the response
                try:
                    # Find JSON in the response (in case there's extra text)
                    start = response_text.find("{")
                    end = response_text.rfind("}") + 1
                    if start != -1 and end != 0:
                        json_str = response_text[start:end]
                        return json.loads(json_str)
                    else:
                        return {
                            "error": "No JSON found in response",
                            "raw_response": response_text,
                        }
                except json.JSONDecodeError as e:
                    return {
                        "error": f"Failed to parse JSON: {e}",
                        "raw_response": response_text,
                    }
            else:
                return {"error": f"Request failed with status {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze a document with Raptor Mini")
    parser.add_argument("file", help="Markdown file to analyze")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File {args.file} not found")
        sys.exit(1)

    content = file_path.read_text()
    analyzer = RaptorAnalyzer()
    result = analyzer.analyze(content)

    if "error" in result:
        print(f"Error: {result['error']}")
        if "raw_response" in result:
            print(f"Raw response: {result['raw_response']}")
        sys.exit(1)

    print(f"Score: {result.get('score', 'N/A')}")
    print("Feedback:")
    for item in result.get("feedback", []):
        print(f"  - {item}")
    print("Suggestions:")
    for item in result.get("suggestions", []):
        print(f"  - {item}")


if __name__ == "__main__":
    main()
