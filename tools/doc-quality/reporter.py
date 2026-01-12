"""
Quality Reporter

This module contains the QualityReporter class that generates
quality reports and summaries from analysis results.
"""

import time
from typing import Dict, Any, List, Optional


class QualityReporter:
    """Generate quality reports and summaries"""

    def __init__(self, results: List[Dict[str, Any]]):
        self.results = results
        self.valid_results = [
            r for r in results if "score" in r and isinstance(r["score"], (int, float))
        ]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.valid_results:
            return {
                "total_files": len(self.results),
                "analyzed_files": 0,
                "average_score": 0,
                "min_score": 0,
                "max_score": 0,
                "high_quality": 0,
                "medium_quality": 0,
                "low_quality": 0,
                "errors": len(self.results),
            }

        scores = [r["score"] for r in self.valid_results]

        return {
            "total_files": len(self.results),
            "analyzed_files": len(self.valid_results),
            "average_score": round(sum(scores) / len(scores), 1),
            "min_score": min(scores),
            "max_score": max(scores),
            "high_quality": len([s for s in scores if s >= 80]),
            "medium_quality": len([s for s in scores if 60 <= s < 80]),
            "low_quality": len([s for s in scores if s < 60]),
            "errors": len(self.results) - len(self.valid_results),
        }

    def get_failed_files(self, min_score: int = 70) -> List[Dict[str, Any]]:
        """Get files that failed quality check"""
        return [r for r in self.valid_results if r.get("score", 0) < min_score]

    def get_top_performers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing files"""
        return sorted(self.valid_results, key=lambda x: x["score"], reverse=True)[
            :limit
        ]

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate detailed report"""
        stats = self.get_summary_stats()
        failed_files = self.get_failed_files()
        top_performers = self.get_top_performers()

        report = []
        report.append("# Documentation Quality Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        report.append("## Summary Statistics")
        report.append(f"- **Total Files**: {stats['total_files']}")
        report.append(f"- **Successfully Analyzed**: {stats['analyzed_files']}")
        report.append(f"- **Average Score**: {stats['average_score']}/100")
        report.append(f"- **Score Range**: {stats['min_score']} - {stats['max_score']}")
        report.append(f"- **High Quality (≥80)**: {stats['high_quality']}")
        report.append(f"- **Medium Quality (60-79)**: {stats['medium_quality']}")
        report.append(f"- **Low Quality (<60)**: {stats['low_quality']}")
        if stats["errors"] > 0:
            report.append(f"- **Errors**: {stats['errors']}")
        report.append("")

        if top_performers:
            report.append("## Top Performing Files")
            for i, result in enumerate(top_performers, 1):
                filename = result.get("filename", result.get("file_path", "unknown"))
                score = result["score"]
                strength = result.get("strength", "unknown")
                report.append(f"{i}. **{filename}**: {score}/100 - {strength}")
            report.append("")

        if failed_files:
            report.append("## Files Needing Improvement")
            for result in failed_files:
                filename = result.get("filename", result.get("file_path", "unknown"))
                score = result["score"]
                weakness = result.get("weakness", "unknown")
                improvements = result.get("improvements", [])
                report.append(f"- **{filename}** ({score}/100): {weakness}")
                if improvements:
                    report.append(f"  - Suggestions: {', '.join(improvements)}")
            report.append("")

        # Individual file results
        report.append("## Individual File Results")
        for result in self.results:
            filename = result.get("filename", result.get("file_path", "unknown"))

            if "error" in result:
                report.append(f"- **{filename}**: ❌ Error - {result['error']}")
            else:
                score = result.get("score", 0)
                strength = result.get("strength", "unknown")
                report.append(f"- **{filename}**: {score}/100 - {strength}")

        report_text = "\n".join(report)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_text)
            print(f"📄 Report saved to: {output_file}")

        return report_text
