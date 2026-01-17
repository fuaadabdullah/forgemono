"""
Command Line Interface

This module contains the CLI interface for the documentation quality checker.
"""

import argparse
import asyncio
import json
import os
import sys
import time

from api_client import APIClient
from quality_analyzer import StandaloneQualityAnalyzer, AdapterEngine
from file_discovery import FileDiscovery
from config_manager import ConfigManager
from reporter import QualityReporter


def main():
    """Main CLI function"""

    # Check environment variables for debug settings
    env_debug = os.getenv("DOC_QUALITY_DEBUG", "").lower() in ("true", "1", "yes")
    env_debug_api = os.getenv("DOC_QUALITY_DEBUG_API", "").lower() in (
        "true",
        "1",
        "yes",
    )
    env_debug_timing = os.getenv("DOC_QUALITY_DEBUG_TIMING", "").lower() in (
        "true",
        "1",
        "yes",
    )
    env_debug_files = os.getenv("DOC_QUALITY_DEBUG_FILES", "").lower() in (
        "true",
        "1",
        "yes",
    )

    parser = argparse.ArgumentParser(
        description="Automated documentation quality checks using Raptor Mini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check all docs in docs/ directory
  python doc_quality_check.py

  # Check specific files
  python doc_quality_check.py docs/README.md docs/WORKSPACE_OVERVIEW.md

  # CI mode with quality gate
  python doc_quality_check.py --ci --min-score 70

  # Generate detailed report
  python doc_quality_check.py --report docs/reports/quality_report.md

  # Check with custom API URL
  python doc_quality_check.py --api-url http://localhost:8000
        """,
    )

    parser.add_argument(
        "files", nargs="*", help="Specific files to check (default: all docs in docs/)"
    )

    parser.add_argument(
        "--api-url",
        default="https://thomasena-auxochromic-joziah.ngrok-free.dev",
        help="Raptor Mini API URL",
    )

    parser.add_argument(
        "--min-score",
        type=int,
        default=60,
        help="Minimum acceptable score (default: 60)",
    )

    parser.add_argument(
        "--report", help="Generate detailed report file (supports .md, .json, .txt)"
    )

    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit with code 1 if quality check fails",
    )

    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Treat scores below 80 as failures",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for processing multiple files",
    )

    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")

    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Run in standalone mode (no external dependencies required)",
    )

    # Debug options
    parser.add_argument(
        "--debug",
        action="store_true",
        default=env_debug,
        help="Enable debug mode with verbose logging",
    )

    parser.add_argument(
        "--debug-api",
        action="store_true",
        default=env_debug_api,
        help="Show detailed API request/response information",
    )

    parser.add_argument(
        "--debug-timing",
        action="store_true",
        default=env_debug_timing,
        help="Show timing information for operations",
    )

    parser.add_argument(
        "--debug-files",
        action="store_true",
        default=env_debug_files,
        help="Show file discovery and processing details",
    )

    parser.add_argument(
        "--save-responses", help="Save raw API responses to specified directory"
    )

    parser.add_argument(
        "--mode",
        default=os.environ.get("RAPTOR_MODE", "dual"),
        choices=["phi_only", "raptor_only", "dual"],
        help="Model orchestration mode: phi_only, raptor_only, or dual",
    )

    parser.add_argument(
        "--config",
        default=os.environ.get(
            "DOC_QUALITY_CONFIG", "tools/doc-quality/doc_quality_config.yaml"
        ),
        help="Path to configuration YAML file",
    )

    parser.add_argument(
        "--soft-fallback",
        action="store_true",
        default=os.environ.get("DOC_QUALITY_SOFT_FALLBACK", "false").lower()
        in ("true", "1", "yes"),
        help="Allow phi_only to soft-fallback to Raptor API if local Phi is down",
    )

    args = parser.parse_args()

    # Initialize components
    try:
        # Load configuration
        config_manager = ConfigManager(config_file=args.config)
        config = config_manager.get_effective_config()

        # Initialize file discovery
        file_discovery_config = config.get("file_discovery", {})
        file_discovery = FileDiscovery(
            extensions=file_discovery_config.get(
                "extensions", [".md", ".txt", ".rst", ".adoc"]
            ),
            debug=args.debug_files,
        )

        # Initialize analyzers based on mode
        if args.standalone or args.mode == "standalone":
            # Use standalone analyzer
            analyzer = StandaloneQualityAnalyzer()
        else:
            # Use adapter engine for API/local models
            analyzer = AdapterEngine(
                config_file=args.config, soft_fallback=args.soft_fallback
            )
            analyzer.initialize()

        # Initialize API client for direct API calls if needed
        api_client = APIClient(
            api_url=args.api_url,
            debug_api=args.debug_api,
            debug_timing=args.debug_timing,
            save_responses_dir=args.save_responses,
        )

    except Exception as e:
        print(f"❌ Failed to initialize quality checker: {e}")
        sys.exit(1)

    # Determine files to check
    if args.files:
        files_to_check = args.files
        if args.debug_files:
            print(f"🐛 Debug: Using {len(files_to_check)} specified files:")
            for f in files_to_check:
                print(f"  • {f}")
    else:
        files_to_check = file_discovery.discover_and_validate()
        if args.debug_files:
            print(
                f"🐛 Debug: Auto-discovered {len(files_to_check)} files in docs/ directory"
            )
            for f in files_to_check[:10]:  # Show first 10
                print(f"  • {f}")
            if len(files_to_check) > 10:
                print(f"  ... and {len(files_to_check) - 10} more")

    if not files_to_check:
        print("❌ No documentation files found to check")
        sys.exit(1)

    if not args.quiet:
        print(f"🔍 Checking {len(files_to_check)} documentation files...")
        print(f"📊 Using API: {args.api_url}")
        print(f"🎯 Minimum score: {args.min_score}")
        print()

    # Analyze files
    analysis_start_time = time.time()

    async def analyze_files():
        results = []
        for file_path in files_to_check:
            try:
                if args.debug_timing:
                    print(f"🐛 Debug: Analyzing {file_path}...")

                if args.standalone or args.mode == "standalone":
                    # Use standalone analyzer
                    result = await analyzer.analyze_file(file_path)
                elif args.mode in ["phi_only", "dual"]:
                    # Use adapter engine
                    result = await analyzer.analyze_file(file_path, mode=args.mode)
                else:
                    # Use direct API calls
                    if len(files_to_check) == 1:
                        result_dict = api_client.analyze_file(file_path)
                        # Convert dict to AnalysisResult
                        from quality_analyzer import AnalysisResult

                        result = AnalysisResult(
                            filename=os.path.basename(file_path),
                            content=result_dict.get("content", ""),
                            provider=result_dict.get("provider", ""),
                            model=result_dict.get("model", ""),
                            score=result_dict.get("score", 0),
                            metadata=result_dict.get("metadata", {}),
                            error=result_dict.get("error"),
                        )
                    else:
                        # For batch, this is more complex - for now use individual API calls
                        result_dict = api_client.analyze_file(file_path)
                        from quality_analyzer import AnalysisResult

                        result = AnalysisResult(
                            filename=os.path.basename(file_path),
                            content=result_dict.get("content", ""),
                            provider=result_dict.get("provider", ""),
                            model=result_dict.get("model", ""),
                            score=result_dict.get("score", 0),
                            metadata=result_dict.get("metadata", {}),
                            error=result_dict.get("error"),
                        )

                results.append(result.to_dict())

            except Exception as e:
                from quality_analyzer import AnalysisResult

                error_result = AnalysisResult(
                    filename=os.path.basename(file_path),
                    error=f"Analysis failed: {str(e)}",
                    score=0,
                )
                results.append(error_result.to_dict())

        return results

    # Run async analysis
    results = asyncio.run(analyze_files())

    analysis_elapsed = time.time() - analysis_start_time

    if args.debug_timing:
        print(f"🐛 Debug: Analysis completed in {analysis_elapsed:.3f}s")
        print(
            f"🐛 Debug: Average time per file: {analysis_elapsed / len(files_to_check):.3f}s"
        )

    if args.debug:
        print("🐛 Debug: Analysis results summary:")
        successful_results = [
            r for r in results if "score" in r and isinstance(r["score"], (int, float))
        ]
        error_results = [r for r in results if "error" in r]
        print(f"  • Total results: {len(results)}")
        print(f"  • Successful analyses: {len(successful_results)}")
        print(f"  • Errors: {len(error_results)}")
        if error_results:
            print("  • Error details:")
            for error_result in error_results[:5]:  # Show first 5 errors
                filename = error_result.get(
                    "filename", error_result.get("file_path", "unknown")
                )
                print(f"    - {filename}: {error_result['error']}")
            if len(error_results) > 5:
                print(f"    ... and {len(error_results) - 5} more errors")
    else:
        # Non-debug mode: just track request count from API client
        if hasattr(api_client, "request_count") and api_client.request_count > 0:
            print(f"🐛 Debug: Total API requests made: {api_client.request_count}")

    # Create reporter
    reporter = QualityReporter(results)
    stats = reporter.get_summary_stats()

    # Output results
    if args.json:
        # JSON output for automation
        output = {
            "timestamp": time.time(),
            "api_url": args.api_url,
            "files_checked": len(files_to_check),
            "statistics": stats,
            "results": results,
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        if not args.quiet:
            print("📊 Quality Check Results")
            print("=" * 40)
            print(f"Files analyzed: {stats['analyzed_files']}/{stats['total_files']}")
            print(f"Average score: {stats['average_score']}/100")
            print(f"Score range: {stats['min_score']} - {stats['max_score']}")
            print(f"High quality (≥80): {stats['high_quality']}")
            print(f"Medium quality (60-79): {stats['medium_quality']}")
            print(f"Low quality (<60): {stats['low_quality']}")
            if stats["errors"] > 0:
                print(f"Errors: {stats['errors']}")
            print()

        # Show failed files
        failed_files = reporter.get_failed_files(args.min_score)
        if failed_files:
            if not args.quiet:
                print("❌ Files below minimum score:")
                for result in failed_files:
                    filename = result.get(
                        "filename", result.get("file_path", "unknown")
                    )
                    score = result["score"]
                    weakness = result.get("weakness", "unknown")
                    print(f"  • {filename}: {score}/100 - {weakness}")
                print()

    # Generate report if requested
    if args.report:
        reporter.generate_report(args.report)
        if not args.quiet:
            print(f"📄 Detailed report saved to: {args.report}")

    # Determine exit code for CI
    min_threshold = 80 if args.fail_on_warnings else args.min_score
    failed_files = reporter.get_failed_files(min_threshold)

    if args.ci and failed_files:
        if not args.quiet:
            print(
                f"❌ Quality check failed: {len(failed_files)} files below threshold ({min_threshold})"
            )
        sys.exit(1)
    elif failed_files:
        if not args.quiet:
            print(
                f"⚠️  Warning: {len(failed_files)} files below recommended threshold ({min_threshold})"
            )
    else:
        if not args.quiet:
            print("✅ All files passed quality check!")
