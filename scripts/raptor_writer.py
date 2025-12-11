#!/usr/bin/env python3
"""
Raptor Mini Document Writer
"""

import requests
from pathlib import Path
import sys


class RaptorWriter:
    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "raptor-mini"
    ):
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": max_tokens,
                    },
                },
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                return f"Error: Request failed with status {response.status_code}"

        except Exception as e:
            return f"Error: {str(e)}"

    def improve(
        self,
        content: str,
        instructions: str = "Improve the clarity and conciseness of this text.",
    ) -> str:
        prompt = f"""{instructions}

        Original text:
        {content}

        Improved text:
        """

        return self.generate(prompt)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate or improve documents with Raptor Mini"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate a document")
    generate_parser.add_argument("prompt", help="Prompt for generation")

    # Improve command
    improve_parser = subparsers.add_parser("improve", help="Improve a document")
    improve_parser.add_argument("file", help="File to improve")
    improve_parser.add_argument(
        "--instructions",
        default="Improve the clarity and conciseness of this text.",
        help="Instructions for improvement",
    )

    args = parser.parse_args()

    writer = RaptorWriter()

    if args.command == "generate":
        result = writer.generate(args.prompt)
        print(result)
    elif args.command == "improve":
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File {args.file} not found")
            sys.exit(1)
        content = file_path.read_text()
        result = writer.improve(content, args.instructions)
        print(result)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
