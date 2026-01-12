"""
File Discovery Module for Documentation Quality Checker
Handles finding and filtering documentation files in directories
"""

import os
from pathlib import Path
from typing import List, Optional


class FileDiscovery:
    """Handles discovery and filtering of documentation files"""

    def __init__(self, extensions: Optional[List[str]] = None, debug: bool = False):
        if extensions is None:
            extensions = [".md", ".txt", ".rst", ".adoc"]
        self.extensions = extensions
        self.debug = debug

    def find_doc_files(
        self, directory: str = "docs", recursive: bool = True
    ) -> List[str]:
        """Find documentation files in directory"""
        if self.debug:
            print(f"🐛 Debug: Searching for documentation files in: {directory}")
            print(f"🐛 Debug: File extensions: {', '.join(self.extensions)}")
            print(f"🐛 Debug: Recursive search: {recursive}")

        doc_files = []
        docs_path = Path(directory)

        if not docs_path.exists():
            if self.debug:
                print(f"🐛 Debug: Directory {directory} does not exist")
            return doc_files

        if recursive:
            # Recursive search
            for ext in self.extensions:
                found_files = list(docs_path.rglob(f"*{ext}"))
                if self.debug:
                    print(
                        f"🐛 Debug: Found {len(found_files)} files with extension {ext}"
                    )
                doc_files.extend(str(p) for p in found_files)
        else:
            # Top-level only search
            for ext in self.extensions:
                found_files = list(docs_path.glob(f"*{ext}"))
                if self.debug:
                    print(
                        f"🐛 Debug: Found {len(found_files)} files with extension {ext}"
                    )
                doc_files.extend(str(p) for p in found_files)

        if self.debug:
            print(f"🐛 Debug: Total files found: {len(doc_files)}")

        return sorted(doc_files)

    def find_files_by_pattern(
        self, directory: str, pattern: str, recursive: bool = True
    ) -> List[str]:
        """Find files matching a specific pattern"""
        if self.debug:
            print(
                f"🐛 Debug: Searching for files with pattern: {pattern} in: {directory}"
            )

        docs_path = Path(directory)

        if not docs_path.exists():
            if self.debug:
                print(f"🐛 Debug: Directory {directory} does not exist")
            return []

        if recursive:
            found_files = list(docs_path.rglob(pattern))
        else:
            found_files = list(docs_path.glob(pattern))

        file_paths = [str(p) for p in found_files]

        if self.debug:
            print(
                f"🐛 Debug: Found {len(file_paths)} files matching pattern '{pattern}'"
            )

        return sorted(file_paths)

    def filter_files_by_size(
        self,
        file_paths: List[str],
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
    ) -> List[str]:
        """Filter files by size in bytes"""
        filtered_files = []

        for file_path in file_paths:
            try:
                size = os.path.getsize(file_path)
                include = True

                if min_size is not None and size < min_size:
                    include = False
                if max_size is not None and size > max_size:
                    include = False

                if include:
                    filtered_files.append(file_path)

            except OSError as e:
                if self.debug:
                    print(f"🐛 Debug: Could not get size for {file_path}: {e}")
                continue

        if self.debug:
            print(
                f"🐛 Debug: Filtered {len(file_paths)} files down to {len(filtered_files)} by size"
            )

        return filtered_files

    def validate_files(self, file_paths: List[str]) -> List[str]:
        """Validate that files exist and are readable"""
        valid_files = []

        for file_path in file_paths:
            if os.path.exists(file_path) and os.access(file_path, os.R_OK):
                valid_files.append(file_path)
            elif self.debug:
                print(f"🐛 Debug: File not accessible: {file_path}")

        if self.debug:
            print(
                f"🐛 Debug: Validated {len(valid_files)} out of {len(file_paths)} files"
            )

        return valid_files

    def get_file_info(self, file_path: str) -> Optional[dict]:
        """Get basic information about a file"""
        try:
            stat = os.stat(file_path)
            return {
                "path": file_path,
                "name": os.path.basename(file_path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "extension": os.path.splitext(file_path)[1],
                "readable": os.access(file_path, os.R_OK),
            }
        except OSError:
            return None

    def discover_and_validate(
        self,
        directory: str = "docs",
        recursive: bool = True,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
    ) -> List[str]:
        """Complete discovery and validation workflow"""
        # Find files
        files = self.find_doc_files(directory, recursive)

        # Filter by size if specified
        if min_size is not None or max_size is not None:
            files = self.filter_files_by_size(files, min_size, max_size)

        # Validate accessibility
        files = self.validate_files(files)

        return files

    def get_discovery_stats(self, file_paths: List[str]) -> dict:
        """Get statistics about discovered files"""
        total_size = 0
        extensions = {}
        sizes = []

        for file_path in file_paths:
            info = self.get_file_info(file_path)
            if info:
                total_size += info["size"]
                sizes.append(info["size"])

                ext = info["extension"]
                extensions[ext] = extensions.get(ext, 0) + 1

        avg_size = total_size / len(file_paths) if file_paths else 0
        min_size = min(sizes) if sizes else 0
        max_size = max(sizes) if sizes else 0

        return {
            "total_files": len(file_paths),
            "total_size": total_size,
            "avg_size": avg_size,
            "min_size": min_size,
            "max_size": max_size,
            "extensions": extensions,
        }
