"""
Standalone Quality Checker

This module contains the StandaloneQualityChecker class that provides
documentation quality analysis using simple heuristics without external dependencies.
"""

import logging
from typing import Dict, Any


class StandaloneQualityChecker:
    """Standalone quality checker that doesn't require external APIs"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_content(
        self, content: str, filename: str = "content.md"
    ) -> Dict[str, Any]:
        """Analyze content using simple heuristics"""
        try:
            # Basic metrics
            lines = content.split("\n")
            sentences = [
                s.strip() for s in content.replace("\n", " ").split(".") if s.strip()
            ]
            words = content.split()
            chars = len(content)

            # Calculate score based on heuristics
            score = 50  # Base score

            # Length bonuses
            if chars > 1000:
                score += 15
            elif chars > 500:
                score += 10
            elif chars > 200:
                score += 5

            # Structure bonuses
            if "#" in content:  # Has headers
                score += 10
            if "`" in content:  # Has code examples
                score += 10
            if "- " in content or "* " in content:  # Has lists
                score += 5

            # Content quality bonuses
            if len(sentences) > 10:
                score += 10
            if len(words) > 100:
                score += 5

            # Readability check (simple)
            avg_words_per_sentence = len(words) / max(len(sentences), 1)
            if 10 <= avg_words_per_sentence <= 25:
                score += 5

            # Cap at 100
            score = min(score, 100)

            # Determine strength/weakness
            if score >= 80:
                strength = "Good structure and content depth"
                weakness = "Could benefit from more specific examples"
                improvements = []
            elif score >= 60:
                strength = "Basic structure present"
                weakness = "Needs more detailed content and examples"
                improvements = [
                    "Add section headers",
                    "Include code examples",
                    "Expand explanations",
                ]
            else:
                strength = "Minimal content"
                weakness = "Significant improvements needed"
                improvements = [
                    "Add comprehensive content",
                    "Include examples",
                    "Improve structure",
                ]

            return {
                "filename": filename,
                "content": f"Quality Score: {score}/100\nStrength: {strength}\nWeakness: {weakness}",
                "provider": "standalone",
                "model": "heuristic_analyzer",
                "score": score,
                "metadata": {
                    "analysis_type": "quality_score",
                    "content_length": chars,
                    "sentence_count": len(sentences),
                    "word_count": len(words),
                    "line_count": len(lines),
                    "raw_response": {
                        "score": score,
                        "strength": strength,
                        "weakness": weakness,
                        "improvements": improvements,
                    },
                },
            }

        except Exception as e:
            return {
                "error": f"Standalone analysis failed: {str(e)}",
                "filename": filename,
                "score": 0,
            }
