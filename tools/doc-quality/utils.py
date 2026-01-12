"""
Utility Functions

This module contains utility functions for the documentation quality checker.
"""

from pathlib import Path
from typing import List


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
