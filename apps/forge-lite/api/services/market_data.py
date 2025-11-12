"""
Market data service for ForgeTM Lite.
Fetches and caches market data from Alpha Vantage and Finnhub for offline-first trading.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import requests
from dotenv import dotenv_values

# Load environment variables from parent directory's .env.local file
env_path = Path(__file__).parent.parent.parent / '.env.local'
env_values = dotenv_values(env_path)

class MarketDataService:
    def __init__(self):
        # Use values from .env.local directly, with fallbacks to environment variables
        self.alpha_vantage_key = env_values.get('ALPHA_VANTAGE_API_KEY') or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.finnhub_key = env_values.get('FINNHUB_API_KEY') or os.getenv('FINNHUB_API_KEY')
        self.polygon_key = env_values.get('POLYGON_API_KEY') or os.getenv('POLYGON_API_KEY')
        self.cache_dir = Path(__file__).parent.parent.parent / 'cache'
        self.cache_dir.mkdir(exist_ok=True)

    def fetch_and_cache_market_data(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Fetch market data for given symbols and cache locally.
        Default symbols include major indices and popular stocks.
        """
        if symbols is None:
            symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

        results = {}
        for symbol in symbols:
            try:
                data = self._fetch_symbol_data(symbol)
                if data:
                    self._cache_symbol_data(symbol, data)
                    results[symbol] = {'status': 'success', 'data': data}
                else:
                    results[symbol] = {'status': 'failed', 'error': 'No data available'}
            except Exception as e:
                results[symbol] = {'status': 'error', 'error': str(e)}

        return results

    def _fetch_symbol_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch data for a single symbol from available providers."""
        # Try Alpha Vantage first
        if self.alpha_vantage_key:
            try:
                return self._fetch_alpha_vantage(symbol)
            except Exception as e:
                print(f"Alpha Vantage failed for {symbol}: {e}")

        # Fallback to Finnhub
        if self.finnhub_key:
            try:
                return self._fetch_finnhub(symbol)
            except Exception as e:
                print(f"Finnhub failed for {symbol}: {e}")

        # Final fallback to Polygon
        if self.polygon_key:
            try:
                return self._fetch_polygon(symbol)
            except Exception as e:
                print(f"Polygon failed for {symbol}: {e}")

        return None

    def _fetch_alpha_vantage(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from Alpha Vantage API."""
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.alpha_vantage_key
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'Global Quote' in data:
            quote = data['Global Quote']
            return {
                'symbol': symbol,
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%'),
                'volume': int(quote.get('06. volume', 0)),
                'last_updated': quote.get('07. latest trading day', ''),
                'source': 'alpha_vantage',
                'timestamp': int(time.time())
            }

        raise ValueError("Invalid response from Alpha Vantage")

    def _fetch_finnhub(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from Finnhub API."""
        url = f"https://finnhub.io/api/v1/quote"
        params = {
            'symbol': symbol,
            'token': self.finnhub_key
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if all(key in data for key in ['c', 'd', 'dp', 'h', 'l', 'o', 'pc', 't']):
            return {
                'symbol': symbol,
                'price': data['c'],  # Current price
                'change': data['d'],  # Change
                'change_percent': f"{data['dp']:.2f}%",  # Change percent
                'high': data['h'],  # High price of the day
                'low': data['l'],  # Low price of the day
                'open': data['o'],  # Open price of the day
                'previous_close': data['pc'],  # Previous close price
                'last_updated': time.strftime('%Y-%m-%d', time.localtime(data['t'])),
                'source': 'finnhub',
                'timestamp': int(time.time())
            }

        raise ValueError("Invalid response from Finnhub")

    def _fetch_polygon(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from Polygon API."""
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
        params = {
            'apiKey': self.polygon_key
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'OK' and data.get('results'):
            result = data['results'][0]
            return {
                'symbol': symbol,
                'price': result['c'],  # Close price
                'open': result['o'],  # Open price
                'high': result['h'],  # High price
                'low': result['l'],  # Low price
                'volume': result['v'],  # Volume
                'change': result['c'] - result['o'],  # Change from open
                'change_percent': f"{((result['c'] - result['o']) / result['o'] * 100):.2f}%" if result['o'] != 0 else "0%",
                'last_updated': time.strftime('%Y-%m-%d', time.localtime(result['t'] / 1000)),  # Convert from milliseconds
                'source': 'polygon',
                'timestamp': int(time.time())
            }

        raise ValueError("Invalid response from Polygon")

    def _cache_symbol_data(self, symbol: str, data: Dict[str, Any]) -> None:
        """Cache symbol data to local file."""
        cache_file = self.cache_dir / f"{symbol.lower()}.json"
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_cached_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached data for a symbol."""
        cache_file = self.cache_dir / f"{symbol.lower()}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def is_cache_stale(self, symbol: str, max_age_hours: int = 24) -> bool:
        """Check if cached data is older than max_age_hours."""
        data = self.get_cached_data(symbol)
        if not data or 'timestamp' not in data:
            return True

        age_seconds = time.time() - data['timestamp']
        return age_seconds > (max_age_hours * 3600)


def fetch_and_cache_market_data():
    """CLI entry point for market data fetching."""
    service = MarketDataService()
    results = service.fetch_and_cache_market_data()

    print("Market Data Fetch Results:")
    print(json.dumps(results, indent=2))

    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    print(f"\nSuccessfully fetched data for {success_count}/{len(results)} symbols")


if __name__ == "__main__":
    fetch_and_cache_market_data()
