#!/usr/bin/env python3
"""
Documentation Quality Check CLI Tool
Automated quality analysis for ForgeMonorepo documentation using Raptor Mini API

Usage:
    python doc_quality_check.py [options] [files...]

Examples:
    # Check all documentation files
    python doc_quality_check.py

    # Check specific files
    python doc_quality_check.py docs/README.md docs/WORKSPACE_OVERVIEW.md

    # Check with custom thresholds
    python doc_quality_check.py --min-score 80 --fail-on-warnings

    # Generate detailed report
    python doc_quality_check.py --report doc_quality_report.json

    # CI mode (non-interactive, exit codes)
    python doc_quality_check.py --ci --min-score 70

    # Debug mode with verbose logging
    python doc_quality_check.py --debug --debug-api --debug-timing

    # Save API responses for debugging
    python doc_quality_check.py --save-responses ./debug_responses

    # STANDALONE MODE - No external dependencies required
    python doc_quality_check.py --standalone
    python doc_quality_check.py docs/*.md --standalone --json
"""

from cli import main

if __name__ == "__main__":
    main()
