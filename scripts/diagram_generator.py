#!/usr/bin/env python3
"""
Mermaid Diagram Generator
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict
import tempfile


class DiagramExtractor:
    def __init__(self):
        self.patterns = {
            "python": r"#\s*mermaid:\s*(.*?)(?:\n#|$)",
            "js": r"//\s*mermaid:\s*(.*?)(?:\n//|$)",
            "go": r"//\s*mermaid:\s*(.*?)(?:\n//|$)",
            "rust": r"//\s*mermaid:\s*(.*?)(?:\n//|$)",
            "sql": r"--\s*mermaid:\s*(.*?)(?:\n--|$)",
            "html": r"<!--\s*mermaid:\s*(.*?)\s*-->",
            "block": r"```mermaid\s*\n(.*?)\n```",
        }

    def extract_from_file(self, file_path: Path) -> List[Dict]:
        if not file_path.exists():
            return []

        content = file_path.read_text()
        diagrams = []

        # Try file extension patterns
        ext = file_path.suffix.lstrip(".")
        if ext in self.patterns:
            for match in re.finditer(self.patterns[ext], content, re.DOTALL):
                diagrams.append(
                    {
                        "file": str(file_path),
                        "code": match.group(1).strip(),
                        "type": "inline",
                    }
                )

        # Also check for markdown-style mermaid blocks (in any file)
        for match in re.finditer(self.patterns["block"], content, re.DOTALL):
            diagrams.append(
                {
                    "file": str(file_path),
                    "code": match.group(1).strip(),
                    "type": "block",
                }
            )

        return diagrams

    def extract_from_directory(self, directory: Path) -> List[Dict]:
        # Handle both files and directories
        if directory.is_file():
            return self.extract_from_file(directory)

        extensions = [".py", ".js", ".ts", ".java", ".go", ".rs", ".sql", ".md", ".txt"]
        diagrams = []

        for ext in extensions:
            for file_path in directory.rglob(f"*{ext}"):
                # Skip node_modules, venv, etc
                if any(
                    ignore in str(file_path)
                    for ignore in ["node_modules", "venv", ".git"]
                ):
                    continue

                file_diagrams = self.extract_from_file(file_path)
                diagrams.extend(file_diagrams)

        return diagrams


class DiagramRenderer:
    def __init__(self, output_dir: Path = Path("docs/diagrams")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render(self, diagram_code: str, output_format: str = "svg") -> Path:
        # Create a temporary file for the mermaid code
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
            f.write(diagram_code)
            input_file = Path(f.name)

        # Generate output file name
        import hashlib

        content_hash = hashlib.md5(diagram_code.encode()).hexdigest()[:8]
        output_file = self.output_dir / f"diagram_{content_hash}.{output_format}"

        # Use mermaid-cli to render
        try:
            subprocess.run(
                [
                    "npx",
                    "mmdc",
                    "-i",
                    str(input_file),
                    "-o",
                    str(output_file),
                    "-t",
                    "default",
                    "-b",
                    "transparent",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error rendering diagram: {e}")
            output_file = None
        finally:
            # Clean up temp file
            input_file.unlink()

        return output_file


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract and render Mermaid diagrams from code"
    )
    parser.add_argument(
        "--scan", action="store_true", help="Scan codebase for diagrams"
    )
    parser.add_argument("--render", action="store_true", help="Render found diagrams")
    parser.add_argument("--path", default=".", help="Path to scan")
    parser.add_argument("--format", default="svg", help="Output format (svg, png, pdf)")

    args = parser.parse_args()

    extractor = DiagramExtractor()
    renderer = DiagramRenderer()

    if args.scan:
        path = Path(args.path)
        diagrams = extractor.extract_from_directory(path)

        print(f"Found {len(diagrams)} diagram(s):")
        for i, diagram in enumerate(diagrams, 1):
            print(f"{i}. {diagram['file']}")
            print(f"   Type: {diagram['type']}")
            print(f"   Code preview: {diagram['code'][:50]}...")

        if args.render:
            print("\nRendering diagrams...")
            for diagram in diagrams:
                output = renderer.render(diagram["code"], args.format)
                if output:
                    print(f"  Rendered: {output}")
                else:
                    print(f"  Failed to render diagram from {diagram['file']}")


if __name__ == "__main__":
    main()
