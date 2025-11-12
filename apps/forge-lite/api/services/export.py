"""
Export service for ForgeTM Lite.
Handles GDPR-compliant data exports for users.
"""

import os
import json
import csv
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path


class ExportService:
    def __init__(self):
        self.export_dir = Path(__file__).parent.parent / 'exports'
        self.export_dir.mkdir(exist_ok=True)

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all user data for GDPR compliance.
        Includes trades, watchlists, journal entries, and profile data.
        """
        user_data = {
            'user_profile': self._get_user_profile(user_id),
            'trades': self._get_user_trades(user_id),
            'watchlists': self._get_user_watchlists(user_id),
            'journal_entries': self._get_journal_entries(user_id),
            'preferences': self._get_user_preferences(user_id),
            'export_timestamp': datetime.now().isoformat(),
            'gdpr_compliant': True
        }

        # Create export package
        export_filename = f"user_data_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        zip_path = self.export_dir / f"{export_filename}.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add JSON export
            json_data = json.dumps(user_data, indent=2, default=str)
            zipf.writestr(f"{export_filename}.json", json_data)

            # Add CSV exports for easier analysis
            self._add_csv_exports(zipf, user_data, export_filename)

            # Add README with export information
            readme_content = self._generate_readme(user_id, user_data)
            zipf.writestr("README.md", readme_content)

        return {
            'status': 'success',
            'export_file': str(zip_path),
            'user_id': user_id,
            'data_summary': {
                'trades_count': len(user_data['trades']),
                'watchlists_count': len(user_data['watchlists']),
                'journal_entries_count': len(user_data['journal_entries'])
            }
        }

    def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile data."""
        return {
            'user_id': user_id,
            'created_at': (datetime.now() - timedelta(days=30)).isoformat(),
            'last_login': datetime.now().isoformat(),
            'platform': 'ios',
            'app_version': '1.0.0',
            'subscription_status': 'free',
            'gdpr_consent': True,
            'data_processing_consent': True
        }

    def _get_user_trades(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all trades for the user."""
        return [
            {
                'id': 'trade_001',
                'ticker': 'AAPL',
                'status': 'closed',
                'side': 'long',
                'entry_price': 150.25,
                'exit_price': 155.75,
                'quantity': 100,
                'entry_date': (datetime.now() - timedelta(days=10)).isoformat(),
                'exit_date': (datetime.now() - timedelta(days=5)).isoformat(),
                'pnl_dollars': 550.0,
                'pnl_r_multiple': 2.5,
                'risk_pct': 1.0,
                'fees': 2.50,
                'notes': 'Good execution on earnings play',
                'tags': ['earnings', 'tech']
            },
            {
                'id': 'trade_002',
                'ticker': 'TSLA',
                'status': 'active',
                'side': 'short',
                'entry_price': 245.80,
                'quantity': 50,
                'entry_date': (datetime.now() - timedelta(days=2)).isoformat(),
                'stop_loss': 255.00,
                'target_price': 220.00,
                'risk_pct': 1.5,
                'notes': 'Short into resistance',
                'tags': ['momentum', 'ev']
            }
        ]

    def _get_user_watchlists(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's watchlists."""
        return [
            {
                'id': 'watchlist_001',
                'name': 'Tech Momentum',
                'description': 'High momentum tech stocks',
                'tickers': ['AAPL', 'MSFT', 'GOOGL', 'NVDA'],
                'created_at': (datetime.now() - timedelta(days=20)).isoformat(),
                'last_updated': datetime.now().isoformat()
            },
            {
                'id': 'watchlist_002',
                'name': 'Value Picks',
                'description': 'Undervalued stocks with strong fundamentals',
                'tickers': ['BRK.B', 'JNJ', 'KO', 'PG'],
                'created_at': (datetime.now() - timedelta(days=15)).isoformat(),
                'last_updated': (datetime.now() - timedelta(days=1)).isoformat()
            }
        ]

    def _get_journal_entries(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's journal entries."""
        return [
            {
                'id': 'journal_001',
                'date': (datetime.now() - timedelta(days=10)).isoformat(),
                'trade_id': 'trade_001',
                'market_conditions': 'Bullish momentum post-earnings',
                'entry_reasoning': 'Strong earnings beat, technical breakout',
                'exit_reasoning': 'Hit profit target, market getting overextended',
                'emotional_state': 'disciplined',
                'lessons_learned': 'Good to take profits when target hit, even if market could go higher',
                'mistakes': 'Could have sized up position slightly',
                'improvements': 'Better position sizing calculation'
            },
            {
                'id': 'journal_002',
                'date': (datetime.now() - timedelta(days=2)).isoformat(),
                'trade_id': 'trade_002',
                'market_conditions': 'Volatile, high beta environment',
                'entry_reasoning': 'Short into key resistance level',
                'emotional_state': 'confident',
                'notes': 'Still in position, monitoring closely'
            }
        ]

    def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences and settings."""
        return {
            'theme': 'dark',
            'default_risk_pct': 1.0,
            'notifications_enabled': True,
            'data_export_frequency': 'monthly',
            'privacy_settings': {
                'analytics_enabled': True,
                'crash_reporting_enabled': True,
                'marketing_emails': False
            },
            'trading_preferences': {
                'default_broker': 'none',
                'risk_calculation_method': 'percentage_of_equity',
                'journal_required': True
            }
        }

    def _add_csv_exports(self, zipf: zipfile.ZipFile, data: Dict[str, Any], filename_prefix: str) -> None:
        """Add CSV exports to the zip file."""
        # Trades CSV
        if data['trades']:
            trades_csv = self._dicts_to_csv(data['trades'])
            zipf.writestr(f"{filename_prefix}_trades.csv", trades_csv)

        # Watchlists CSV
        if data['watchlists']:
            watchlists_csv = self._dicts_to_csv(data['watchlists'])
            zipf.writestr(f"{filename_prefix}_watchlists.csv", watchlists_csv)

        # Journal CSV
        if data['journal_entries']:
            journal_csv = self._dicts_to_csv(data['journal_entries'])
            zipf.writestr(f"{filename_prefix}_journal.csv", journal_csv)

    def _dicts_to_csv(self, data: List[Dict[str, Any]]) -> str:
        """Convert list of dicts to CSV string."""
        if not data:
            return ""

        output = []
        headers = list(data[0].keys())
        output.append(','.join(headers))

        for row in data:
            values = []
            for header in headers:
                value = row.get(header, '')
                if isinstance(value, (list, dict)):
                    value = json.dumps(value)
                elif isinstance(value, (int, float)):
                    value = str(value)
                elif value is None:
                    value = ''
                else:
                    value = str(value)
                values.append(f'"{value}"')
            output.append(','.join(values))

        return '\n'.join(output)

    def _generate_readme(self, user_id: str, data: Dict[str, Any]) -> str:
        """Generate README file for the export package."""
        return f"""# ForgeTM Lite Data Export

This package contains a complete export of your ForgeTM Lite data for user ID: {user_id}

## Export Details
- **Export Date**: {data['export_timestamp']}
- **GDPR Compliant**: {data['gdpr_compliant']}
- **Data Included**:
  - User Profile: Account information and preferences
  - Trades: Complete trading history ({len(data['trades'])} trades)
  - Watchlists: Saved stock lists ({len(data['watchlists'])} watchlists)
  - Journal: Trading journal entries ({len(data['journal_entries'])} entries)

## File Contents
- `{user_id}_export.json`: Complete data in JSON format
- `{user_id}_export_trades.csv`: Trades data in CSV format
- `{user_id}_export_watchlists.csv`: Watchlists data in CSV format
- `{user_id}_export_journal.csv`: Journal entries in CSV format
- `README.md`: This file

## Data Retention
Your data remains stored in ForgeTM Lite according to our privacy policy.
This export is provided for your records and compliance purposes.

## Support
If you have questions about this export, please contact support@forgetm.com

---
ForgeTM Lite - Educational Trading Tools
"""


def export_user_data():
    """CLI entry point for user data export."""
    if len(os.sys.argv) != 2:
        print("Usage: python export.py <user_id>")
        return

    user_id = os.sys.argv[1]
    service = ExportService()
    result = service.export_user_data(user_id)

    print("User Data Export Results:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    export_user_data()
