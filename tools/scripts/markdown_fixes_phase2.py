#!/usr/bin/env python3
"""Phase 2: conservative automated Markdown fixes (safe heuristics)

- Add language to fenced code blocks when we can confidently detect it
- Remove trailing punctuation (colon) from headings
- Normalize table pipes to have a single space on each side (improves MD060)
- Optionally normalize ordered list prefixes to "1." style (configurable)

Run with --dry to only list affected files.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import Iterable


FENCE_OPEN_RE = re.compile(r"^(?P<indent>\s*)(?P<fence>`{3,}|~{3,})(?P<lang>\w+)?\s*$")
FENCE_CLOSE_RE = re.compile(r"^(?P<indent>\s*)(?P<fence>`{3,}|~{3,})\s*$")
HEADING_RE = re.compile(r"^(?P<prefix>#{1,6}\s+)(?P<rest>.*?)(?P<punct>[:\-–—])?$")
TABLE_PIPE_RE = re.compile(r"\s*\|\s*")
ORDERED_LIST_RE = re.compile(r"^(?P<indent>\s*)(?P<num>\d+)\.(\s+)")


def detect_fence_language(lines: list[str], start: int, end: int) -> str | None:
    """Heuristic detection: prefer bash for typical shell commands, json/yaml for structured data."""
    for i in range(start, min(end, start + 20)):
        line = lines[i].strip()
        if not line:
            continue
        if line.startswith("{") or line.startswith("["):
            return "json"
        if line.startswith("---") or ":" in line and not line.startswith("//"):
            # YAML heuristic -- only if colon present and appears like key: value
            if re.match(r"^[\w\-]+:\s+", line):
                return "yaml"
        # shell command heuristics
        if re.match(r"^\$\s+", line) or re.match(
            r"^(npm|pip|curl|docker|kubectl|git|make)\b", line
        ):
            return "bash"
        # small JSON-like object
        if line.startswith('"') and ":" in line:
            return "json"
        break
    return None


def fix_text(text: str, normalize_ordered: bool = False) -> tuple[str, list[str]]:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Heading punctuation removal
        m_h = HEADING_RE.match(line)
        if m_h:
            prefix = m_h.group("prefix")
            rest = m_h.group("rest")
            punct = m_h.group("punct")
            if punct is not None and (punct == ":" or punct in "–—-"):
                new_line = f"{prefix}{rest.rstrip()}"
                if new_line != line:
                    line = new_line
        # Fence handling
        m_f = FENCE_OPEN_RE.match(line)
        if m_f:
            indent = m_f.group("indent")
            fence = m_f.group("fence")
            lang = m_f.group("lang")
            # find closing fence
            j = i + 1
            while j < len(lines):
                if FENCE_CLOSE_RE.match(lines[j]):
                    break
                j += 1
            # if no lang and we can detect, add it
            if not lang:
                lang_guess = detect_fence_language(lines, i + 1, j)
                if lang_guess:
                    line = f"{indent}{fence}{lang_guess}"
        # Table spacing
        if (
            "|" in line
            and not line.strip().startswith("|-")
            and not line.strip().startswith("```")
        ):
            # only modify lines that look like tables (at least one pipe and not in code)
            # normalize spaces around pipes
            new_line = re.sub(r"\s*\|\s*", " | ", line)
            if new_line != line:
                line = new_line
        # Ordered list normalization
        if normalize_ordered:
            m_o = ORDERED_LIST_RE.match(line)
            if m_o:
                indent = m_o.group("indent")
                rest = line[m_o.end() :]
                new_line = f"{indent}1. {rest}"
                if new_line != line:
                    line = new_line

        out.append(line)
        i += 1

    new_text = "\n".join(out) + ("\n" if text.endswith("\n") else "")
    diffs = []
    if new_text != text:
        # We'll leave file writing to caller; report single synthetic diff note
        diffs.append("modified")
    return new_text, diffs


def find_targets(root: pathlib.Path, paths: Iterable[str] | None) -> list[pathlib.Path]:
    if paths:
        found = []
        for p in paths:
            base = root / p
            if base.is_dir():
                found.extend(sorted(base.rglob("*.md")))
            elif base.is_file():
                found.append(base)
        return [
            p for p in found if ".git" not in p.parts and "node_modules" not in p.parts
        ]
    # default: operate on tools/, infra/, scripts/
    dirs = ["tools", "infra", "scripts"]
    files = []
    for d in dirs:
        for p in (root / d).rglob("*.md"):
            if ".git" in p.parts or "node_modules" in p.parts:
                continue
            files.append(p)
    return sorted(files)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="Do not write files, only list")
    ap.add_argument(
        "--normalize-ordered",
        action="store_true",
        help="Normalize ordered list prefixes to 1.",
    )
    ap.add_argument("paths", nargs="*", help="Optional files or directories to target")
    args = ap.parse_args()

    root = pathlib.Path.cwd()
    files = find_targets(root, args.paths if args.paths else None)
    modified = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        new_text, diffs = fix_text(text, normalize_ordered=args.normalize_ordered)
        if diffs:
            modified.append(str(f))
            if not args.dry:
                f.write_text(new_text, encoding="utf-8")

    if modified:
        print("Would modify:" if args.dry else "Modified:")
        for m in modified:
            print(" -", m)
    else:
        print("No files modified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
