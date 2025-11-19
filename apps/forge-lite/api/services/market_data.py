"""
Market data service for ForgeTM Lite.
Fetches and caches market data using the GoblinOS ingestion package.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from goblinos_ingestion_market_data import create_market_data_provider, MarketQuote

# Load environment variables from parent directory's .env.local file
env_path = Path(__file__).parent.parent.parent / ".env.local"
from dotenv import dotenv_values

env_values = dotenv_values(env_path)


class MarketDataService:
    """Market data service using GoblinOS ingestion package."""

    def __init__(self):
        # Create market data provider with API keys from environment
        config = {
            "alpha_vantage_key": env_values.get("ALPHA_VANTAGE_API_KEY")
            or os.getenv("ALPHA_VANTAGE_API_KEY"),
            "finnhub_key": env_values.get("FINNHUB_API_KEY")
            or os.getenv("FINNHUB_API_KEY"),
            "polygon_key": env_values.get("POLYGON_API_KEY")
            or os.getenv("POLYGON_API_KEY"),
        }

        self.provider = create_market_data_provider(config)
        self.cache_dir = Path(__file__).parent.parent.parent / "cache"
        self.cache_dir.mkdir(exist_ok=True)

    def fetch_and_cache_market_data(
        self, symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch market data for given symbols and cache locally.
        Default symbols include major indices and popular stocks.
        """
        if symbols is None:
            symbols = ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

        results = {}
        for symbol in symbols:
            try:
                # Use the ingestion package to get quote
                quote = self.provider.get_quote(symbol)
                if quote:
                    self._cache_symbol_data(symbol, self._quote_to_legacy_format(quote))
                    results[symbol] = {
                        "status": "success",
                        "data": self._quote_to_legacy_format(quote),
                    }
                else:
                    results[symbol] = {"status": "failed", "error": "No data available"}
            except Exception as e:
                results[symbol] = {"status": "error", "error": str(e)}

        return results

    def _quote_to_legacy_format(self, quote: MarketQuote) -> Dict[str, Any]:
        """Convert MarketQuote to the legacy format expected by existing code."""
        return {
            "symbol": quote["symbol"],
            "price": quote["price"],
            "change": quote["change"],
            "change_percent": quote["change_percent"],
            "volume": quote["volume"],
            "last_updated": time.strftime(
                "%Y-%m-%d", time.localtime(quote["timestamp"])
            ),
            "source": quote["source"],
            "timestamp": quote["timestamp"],
        }

    def _cache_symbol_data(self, symbol: str, data: Dict[str, Any]) -> None:
        """Cache symbol data to local file."""
        cache_file = self.cache_dir / f"{symbol.lower()}.json"
        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_cached_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached data for a symbol."""
        cache_file = self.cache_dir / f"{symbol.lower()}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def is_cache_stale(self, symbol: str, max_age_hours: int = 24) -> bool:
        """Check if cached data is older than max_age_hours."""
        data = self.get_cached_data(symbol)
        if not data or "timestamp" not in data:
            return True

        age_seconds = time.time() - data["timestamp"]
        return age_seconds > (max_age_hours * 3600)


def fetch_and_cache_market_data():
    """CLI entry point for market data fetching."""
    service = MarketDataService()
    results = service.fetch_and_cache_market_data()

    print("Market Data Fetch Results:")
    print(json.dumps(results, indent=2))

    success_count = sum(1 for r in results.values() if r["status"] == "success")
    print(f"\nSuccessfully fetched data for {success_count}/{len(results)} symbols")


if __name__ == "__main__":
    fetch_and_cache_market_data()
