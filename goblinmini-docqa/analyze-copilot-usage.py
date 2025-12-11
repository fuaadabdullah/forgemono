#!/usr/bin/env python3
"""
Copilot Usage Analyzer for Goblin DocQA
Analyzes token usage patterns and provides optimization recommendations.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List
import redis
from dotenv import load_dotenv

load_dotenv()


class CopilotUsageAnalyzer:
    def __init__(self):
        self.redis_client = None
        self.metrics_url = os.getenv("METRICS_URL", "http://localhost:8000/metrics")

        # Initialize Redis
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            print(f"⚠️  Redis not available: {e}")

    def get_current_metrics(self) -> Dict:
        """Fetch current Prometheus metrics."""
        try:
            response = requests.get(self.metrics_url, timeout=5)
            response.raise_for_status()

            metrics = {}
            for line in response.text.split("\n"):
                if line.startswith("goblin_docqa_copilot_tokens_used_total"):
                    # Parse metric line
                    parts = line.split()
                    if len(parts) >= 2:
                        value = float(parts[1])
                        metrics["total_tokens_used"] = value
                elif line.startswith("goblin_docqa_copilot_requests_total"):
                    parts = line.split()
                    if len(parts) >= 2:
                        value = float(parts[1])
                        metrics["total_requests"] = value

            return metrics
        except Exception as e:
            print(f"⚠️  Could not fetch metrics: {e}")
            return {}

    def get_daily_usage(self, days: int = 7) -> List[Dict]:
        """Get daily token usage from Redis."""
        if not self.redis_client:
            return []

        usage_data = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            used_key = f"copilot_used:{date}"

            try:
                tokens_used = int(self.redis_client.get(used_key) or 0)
                usage_data.append({"date": date, "tokens_used": tokens_used})
            except Exception:
                continue

        return usage_data

    def analyze_usage_patterns(self) -> Dict:
        """Analyze usage patterns and provide recommendations."""
        metrics = self.get_current_metrics()
        daily_usage = self.get_daily_usage()

        analysis = {
            "current_metrics": metrics,
            "daily_usage": daily_usage,
            "recommendations": [],
        }

        # Calculate averages
        if daily_usage:
            total_tokens = sum(day["tokens_used"] for day in daily_usage)
            avg_daily = total_tokens / len(daily_usage)
            analysis["avg_daily_tokens"] = avg_daily

            # Check for spikes
            max_day = max(daily_usage, key=lambda x: x["tokens_used"])
            if max_day["tokens_used"] > avg_daily * 2:
                analysis["recommendations"].append(
                    f"High usage spike on {max_day['date']}: {max_day['tokens_used']} tokens "
                    f"({max_day['tokens_used'] / avg_daily:.1f}x average)"
                )

        # Token efficiency analysis
        total_requests = metrics.get("total_requests", 0)
        total_tokens = metrics.get("total_tokens_used", 0)

        if total_requests > 0:
            avg_tokens_per_request = total_tokens / total_requests
            analysis["avg_tokens_per_request"] = avg_tokens_per_request

            # Recommendations based on token efficiency
            if avg_tokens_per_request > 1000:
                analysis["recommendations"].append(
                    f"High token usage per request ({avg_tokens_per_request:.0f}). "
                    "Consider caching or reducing content size."
                )
            elif avg_tokens_per_request < 100:
                analysis["recommendations"].append(
                    f"Efficient token usage ({avg_tokens_per_request:.0f} per request). Good job!"
                )

        # Budget analysis
        budget_daily = int(os.getenv("COPILOT_TOKEN_BUDGET_DAILY", "100000"))
        if daily_usage:
            latest_usage = daily_usage[0]["tokens_used"]  # Most recent day
            budget_used_pct = (latest_usage / budget_daily) * 100

            if budget_used_pct > 80:
                analysis["recommendations"].append(
                    f"Daily budget usage high: {budget_used_pct:.1f}% ({latest_usage}/{budget_daily})"
                )

        return analysis

    def print_report(self):
        """Print usage analysis report."""
        print("🔍 Copilot Usage Analysis Report")
        print("=" * 50)

        analysis = self.analyze_usage_patterns()

        # Current metrics
        metrics = analysis.get("current_metrics", {})
        if metrics:
            print("📊 Current Metrics:")
            print(f"   Total tokens used: {metrics.get('total_tokens_used', 0):,.0f}")
            print(f"   Total requests: {metrics.get('total_requests', 0):,.0f}")
        else:
            print("⚠️  No current metrics available")

        # Daily usage
        daily_usage = analysis.get("daily_usage", [])
        if daily_usage:
            print("\n📅 Daily Usage (last 7 days):")
            for day in daily_usage[:7]:  # Show last 7 days
                print(f"   {day['date']}: {day['tokens_used']:,.0f} tokens")
        else:
            print("\n📅 No daily usage data available")

        # Averages
        if "avg_daily_tokens" in analysis:
            print(f"\n📈 Average daily tokens: {analysis['avg_daily_tokens']:,.0f}")

        if "avg_tokens_per_request" in analysis:
            print(
                f"📈 Average tokens per request: {analysis['avg_tokens_per_request']:.1f}"
            )

        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            print("\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   • {rec}")
        else:
            print("\n✅ No optimization recommendations at this time")

        print("\n🔧 Optimization Tips:")
        print("   • Enable caching: Set COPILOT_CACHE_ENABLED=true")
        print("   • Adjust budget: Set COPILOT_TOKEN_BUDGET_DAILY=<limit>")
        print("   • Monitor alerts: Check Prometheus for usage alerts")
        print("   • Batch requests: Combine multiple small analyses")


def main():
    analyzer = CopilotUsageAnalyzer()
    analyzer.print_report()


if __name__ == "__main__":
    main()
