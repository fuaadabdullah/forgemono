#!/usr/bin/env python3
"""Apply a small set of safe, repo-wide Markdown fixes:

- Wrap bare-URL-only lines in angle brackets: https://example.com -> <https://example.com>
- Ensure blank lines around headings (one blank line before heading)
- Ensure fenced code blocks are surrounded by blank lines
- Ensure a blank line before list items when not already in a list

This intentionally keeps logic conservative and skips transformations inside fenced code blocks.
"""

from __future__ import annotations

import pathlib
import re
import sys


URL_ONLY_RE = re.compile(r"^\s*(https?://\S+)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+")
LIST_ITEM_RE = re.compile(r"^\s*([-*+] |\d+\.)")
FENCE_RE = re.compile(r"^\s*(```|~~~)\b")


def fix_file(path: pathlib.Path) -> bool:
    changed = False
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    out_lines: list[str] = []
    in_fence = False
    fence_marker = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Fence handling
        m_fence = FENCE_RE.match(line)
        if m_fence:
            marker = m_fence.group(1)
            # ensure blank line before opening fence
            if out_lines and out_lines[-1].strip() != "":
                out_lines.append("")
            out_lines.append(line)
            i += 1
            # copy until closing fence
            while i < len(lines):
                out_lines.append(lines[i])
                if FENCE_RE.match(lines[i]):
                    # ensure a blank line after closing fence (if next line not blank)
                    if i + 1 < len(lines) and lines[i + 1].strip() != "":
                        out_lines.append("")
                    i += 1
                    break
                i += 1
            continue

        # Heading: ensure blank line before
        if HEADING_RE.match(line):
            if out_lines and out_lines[-1].strip() != "":
                out_lines.append("")
            out_lines.append(line)
            i += 1
            continue

        # URL-only lines: wrap in angle brackets
        m_url = URL_ONLY_RE.match(line)
        if m_url:
            url = m_url.group(1)
            new_line = f"<{url}>"
            if new_line != line:
                line = new_line
                changed = True
            out_lines.append(line)
            i += 1
            continue

        # Inline bare URLs (not inside parentheses or already wrapped) - wrap them
        if "http" in line and "<http" not in line:
            # replace http(s) URLs that are not immediately preceded by '(', '<', or '['
            new_line = re.sub(
                r"(?<![\(<\[])https?://\S+", lambda m: f"<{m.group(0)}>", line
            )
            if new_line != line:
                line = new_line
                changed = True

        # List items: ensure blank line before lists (unless continuing a list)
        if LIST_ITEM_RE.match(line):
            if (
                out_lines
                and out_lines[-1].strip() != ""
                and not LIST_ITEM_RE.match(out_lines[-1])
            ):
                out_lines.append("")
            out_lines.append(line)
            i += 1
            continue

        out_lines.append(line)
        i += 1

    new_text = "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def find_md_files(root: pathlib.Path) -> list[pathlib.Path]:
    files = []
    for p in root.rglob("*.md"):
        # skip common vendored and build folders
        skip_parts = {"node_modules", ".git", ".pnpm", "dist", "build", "venv"}
        if any(part in skip_parts for part in p.parts):
            continue
        files.append(p)
    return files


def main() -> int:
    root = pathlib.Path.cwd()
    files = find_md_files(root)
    changed_files = []
    for f in files:
        if fix_file(f):
            changed_files.append(str(f))

    if changed_files:
        print("Modified files:")
        for f in changed_files:
            print(f" - {f}")
        return 0
    print("No changes applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
