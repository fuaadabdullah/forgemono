#!/usr/bin/env python3
"""
Modular Documentation Quality Checker
Refactored version of doc_quality_check_old.py with clean modular architecture

This script demonstrates the new modular structure by orchestrating
all the individual modules: api_client, quality_analyzer, file_discovery,
config_manager, and reporter.
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from api_client import APIClient
from quality_analyzer import StandaloneQualityAnalyzer, AdapterEngine, AnalysisResult
from file_discovery import FileDiscovery
from config_manager import ConfigManager
from reporter import QualityReporter


class ModularDocQualityChecker:
    """Main orchestrator for the modular documentation quality checker"""

    def __init__(
        self,
        api_url: str = "https://thomasena-auxochromic-joziah.ngrok-free.dev",
        mode: str = "standalone",
        config_file: str = None,
        debug: bool = False,
        debug_api: bool = False,
        debug_timing: bool = False,
        debug_files: bool = False,
    ):
        self.api_url = api_url
        self.mode = mode
        self.config_file = config_file
        self.debug = debug
        self.debug_api = debug_api
        self.debug_timing = debug_timing
        self.debug_files = debug_files

        # Initialize components
        self._init_components()

    def _init_components(self):
        """Initialize all modular components"""
        try:
            # Configuration management
            self.config_manager = ConfigManager(config_file=self.config_file)
            self.config = self.config_manager.get_effective_config()

            # File discovery
            file_discovery_config = self.config.get("file_discovery", {})
            self.file_discovery = FileDiscovery(
                extensions=file_discovery_config.get(
                    "extensions", [".md", ".txt", ".rst", ".adoc"]
                ),
                debug=self.debug_files,
            )

            # Quality analyzer based on mode
            if self.mode == "standalone":
                self.analyzer = StandaloneQualityAnalyzer()
            else:
                self.analyzer = AdapterEngine(
                    config_file=self.config_file,
                    soft_fallback=self.config.get("soft_fallback", False),
                )
                self.analyzer.initialize()

            # API client for direct API calls
            self.api_client = APIClient(
                api_url=self.api_url,
                debug_api=self.debug_api,
                debug_timing=self.debug_timing,
                save_responses_dir=None,  # Can be configured later
            )

            # Reporter
            self.reporter = None  # Will be created after analysis

        except Exception as e:
            print(f"❌ Failed to initialize modular checker: {e}")
            raise

    async def analyze_files(self, file_paths: list) -> list:
        """Analyze multiple files using the modular components"""
        results = []

        for file_path in file_paths:
            try:
                if self.debug_timing:
                    print(f"🐛 Debug: Analyzing {file_path}...")

                if self.mode == "standalone":
                    # Use standalone analyzer
                    result = await self.analyzer.analyze_file(file_path)
                elif self.mode in ["phi_only", "dual"]:
                    # Use adapter engine
                    result = await self.analyzer.analyze_file(file_path, mode=self.mode)
                else:
                    # Use direct API calls
                    result_dict = self.api_client.analyze_file(file_path)
                    result = AnalysisResult(
                        filename=file_path,
                        content=result_dict.get("content", ""),
                        provider=result_dict.get("provider", ""),
                        model=result_dict.get("model", ""),
                        score=result_dict.get("score", 0),
                        metadata=result_dict.get("metadata", {}),
                        error=result_dict.get("error"),
                    )

                results.append(result.to_dict())

            except Exception as e:
                error_result = AnalysisResult(
                    filename=file_path,
                    error=f"Analysis failed: {str(e)}",
                    score=0,
                )
                results.append(error_result.to_dict())

        return results

    def discover_files(self, directory: str = "docs") -> list:
        """Discover documentation files using the file discovery module"""
        return self.file_discovery.discover_and_validate(directory)

    def generate_report(self, results: list, output_file: str = None):
        """Generate quality report using the reporter module"""
        self.reporter = QualityReporter(results)

        if output_file:
            self.reporter.generate_report(output_file)
            print(f"📄 Report saved to: {output_file}")

        return self.reporter

    def get_summary_stats(self, results: list = None) -> dict:
        """Get summary statistics"""
        if results and not self.reporter:
            self.reporter = QualityReporter(results)

        if self.reporter:
            return self.reporter.get_summary_stats()

        return {}

    def print_summary(self, results: list):
        """Print a summary of the analysis results"""
        if not results:
            print("No results to summarize")
            return

        stats = self.get_summary_stats(results)

        print("📊 Modular Quality Check Results")
        print("=" * 45)
        print(f"Files analyzed: {stats['analyzed_files']}/{stats['total_files']}")
        print(f"Average score: {stats['average_score']}/100")
        print(f"Score range: {stats['min_score']} - {stats['max_score']}")
        print(f"High quality (≥80): {stats['high_quality']}")
        print(f"Medium quality (60-79): {stats['medium_quality']}")
        print(f"Low quality (<60): {stats['low_quality']}")
        if stats["errors"] > 0:
            print(f"Errors: {stats['errors']}")

        # Show failed files
        failed_files = self.reporter.get_failed_files(60)  # Default threshold
        if failed_files:
            print("\n❌ Files below minimum score:")
            for result in failed_files[:5]:  # Show first 5
                filename = result.get("filename", result.get("file_path", "unknown"))
                score = result["score"]
                weakness = result.get("weakness", "unknown")
                print(f"  • {filename}: {score}/100 - {weakness}")
            if len(failed_files) > 5:
                print(f"  ... and {len(failed_files) - 5} more")


async def main():
    """Main function demonstrating the modular architecture"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Modular Documentation Quality Checker - Clean Architecture Demo"
    )

    parser.add_argument("files", nargs="*", help="Specific files to check")

    parser.add_argument(
        "--directory",
        "-d",
        default="docs",
        help="Directory to scan for documentation files",
    )

    parser.add_argument(
        "--mode",
        default="standalone",
        choices=["standalone", "phi_only", "raptor_only", "dual"],
        help="Analysis mode",
    )

    parser.add_argument("--config", help="Configuration file path")

    parser.add_argument(
        "--api-url",
        default="https://thomasena-auxochromic-joziah.ngrok-free.dev",
        help="API URL for external analysis",
    )

    parser.add_argument("--report", help="Generate report file")

    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    try:
        # Initialize the modular checker
        checker = ModularDocQualityChecker(
            api_url=args.api_url,
            mode=args.mode,
            config_file=args.config,
            debug=args.debug,
            debug_files=args.debug,
            debug_api=args.debug,
            debug_timing=args.debug,
        )

        # Discover or use specified files
        if args.files:
            files_to_check = args.files
        else:
            files_to_check = checker.discover_files(args.directory)

        if not files_to_check:
            print("❌ No documentation files found to check")
            return 1

        print(f"🔍 Checking {len(files_to_check)} documentation files...")
        print(f"📊 Using mode: {args.mode}")

        # Analyze files
        results = await checker.analyze_files(files_to_check)

        # Generate report if requested
        if args.report:
            checker.generate_report(results, args.report)

        # Print summary
        checker.print_summary(results)

        # Check for failures
        stats = checker.get_summary_stats(results)
        failed_files = checker.reporter.get_failed_files(60)

        if failed_files:
            print(f"\n⚠️  {len(failed_files)} files below quality threshold")
            return 1
        else:
            print("\n✅ All files passed quality check!")
            return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
