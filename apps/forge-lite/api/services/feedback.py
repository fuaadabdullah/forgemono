"""
Feedback service for ForgeTM Lite.
Exports user feedback, bug reports, and feature requests for analysis.
"""

import os
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

class FeedbackService:
    def __init__(self):
        self.db_path = os.getenv('DATABASE_URL', 'sqlite:./data/forge_lite.db')
        self.export_dir = Path(__file__).parent.parent / 'exports'
        self.export_dir.mkdir(exist_ok=True)

    def export_feedback(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Export user feedback, bug reports, and feature requests from the last N days.
        """
        since_date = datetime.now() - timedelta(days=days_back)

        results = {
            'bug_reports': self._export_bug_reports(since_date),
            'feature_requests': self._export_feature_requests(since_date),
            'user_feedback': self._export_user_feedback(since_date),
            'app_ratings': self._export_app_ratings(since_date),
            'export_timestamp': datetime.now().isoformat(),
            'period_days': days_back
        }

        # Save to JSON file
        export_file = self.export_dir / f"feedback_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        # Save to CSV files for easier analysis
        self._export_to_csv(results)

        return {
            'status': 'success',
            'export_file': str(export_file),
            'summary': {
                'bug_reports_count': len(results['bug_reports']),
                'feature_requests_count': len(results['feature_requests']),
                'user_feedback_count': len(results['user_feedback']),
                'app_ratings_count': len(results['app_ratings'])
            }
        }

    def _export_bug_reports(self, since_date: datetime) -> List[Dict[str, Any]]:
        """Export bug reports from database."""
        # This would connect to your actual database
        # For now, return mock data structure
        return [
            {
                'id': 'bug_001',
                'user_id': 'user_123',
                'title': 'Risk calculation shows wrong position size',
                'description': 'When calculating position size for AAPL, the result is 10x higher than expected',
                'severity': 'high',
                'status': 'open',
                'platform': 'ios',
                'app_version': '1.0.0',
                'reported_at': (datetime.now() - timedelta(days=2)).isoformat(),
                'steps_to_reproduce': '1. Enter entry price 150, stop 145, equity 10000, risk 1%',
                'expected_behavior': 'Position size should be ~690 shares',
                'actual_behavior': 'Shows 6900 shares'
            }
        ]

    def _export_feature_requests(self, since_date: datetime) -> List[Dict[str, Any]]:
        """Export feature requests from database."""
        return [
            {
                'id': 'feature_001',
                'user_id': 'user_456',
                'title': 'Add dark mode toggle',
                'description': 'Please add a toggle to switch between light and dark themes',
                'category': 'ui/ux',
                'priority': 'medium',
                'votes': 15,
                'status': 'planned',
                'requested_at': (datetime.now() - timedelta(days=5)).isoformat()
            },
            {
                'id': 'feature_002',
                'user_id': 'user_789',
                'title': 'Export trades to Excel',
                'description': 'Allow exporting trade journal to Excel format for analysis in spreadsheets',
                'category': 'export',
                'priority': 'high',
                'votes': 32,
                'status': 'in_development',
                'requested_at': (datetime.now() - timedelta(days=1)).isoformat()
            }
        ]

    def _export_user_feedback(self, since_date: datetime) -> List[Dict[str, Any]]:
        """Export general user feedback from database."""
        return [
            {
                'id': 'feedback_001',
                'user_id': 'user_101',
                'type': 'general',
                'rating': 4,
                'comment': 'Great app for learning risk management. The R-multiple calculations are very helpful.',
                'submitted_at': (datetime.now() - timedelta(days=3)).isoformat(),
                'platform': 'android',
                'app_version': '1.0.0'
            },
            {
                'id': 'feedback_002',
                'user_id': 'user_202',
                'type': 'usability',
                'rating': 3,
                'comment': 'The interface is clean but could use more guidance for beginners.',
                'submitted_at': (datetime.now() - timedelta(days=7)).isoformat(),
                'platform': 'web',
                'app_version': '1.0.0'
            }
        ]

    def _export_app_ratings(self, since_date: datetime) -> List[Dict[str, Any]]:
        """Export app store ratings and reviews."""
        return [
            {
                'id': 'rating_001',
                'store': 'app_store',
                'rating': 5,
                'title': 'Perfect for student traders',
                'review': 'This app teaches proper risk management without being a broker. Love the offline-first approach!',
                'version': '1.0.0',
                'country': 'US',
                'submitted_at': (datetime.now() - timedelta(days=4)).isoformat()
            },
            {
                'id': 'rating_002',
                'store': 'play_store',
                'rating': 4,
                'title': 'Good foundation, needs more features',
                'review': 'Solid risk calculator. Would love to see more advanced position sizing options.',
                'version': '1.0.0',
                'country': 'CA',
                'submitted_at': (datetime.now() - timedelta(days=6)).isoformat()
            }
        ]

    def _export_to_csv(self, data: Dict[str, Any]) -> None:
        """Export data to CSV files for easier analysis."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Bug reports CSV
        if data['bug_reports']:
            bug_file = self.export_dir / f"bug_reports_{timestamp}.csv"
            with open(bug_file, 'w', newline='') as f:
                if data['bug_reports']:
                    writer = csv.DictWriter(f, fieldnames=data['bug_reports'][0].keys())
                    writer.writeheader()
                    writer.writerows(data['bug_reports'])

        # Feature requests CSV
        if data['feature_requests']:
            feature_file = self.export_dir / f"feature_requests_{timestamp}.csv"
            with open(feature_file, 'w', newline='') as f:
                if data['feature_requests']:
                    writer = csv.DictWriter(f, fieldnames=data['feature_requests'][0].keys())
                    writer.writeheader()
                    writer.writerows(data['feature_requests'])

        # User feedback CSV
        if data['user_feedback']:
            feedback_file = self.export_dir / f"user_feedback_{timestamp}.csv"
            with open(feedback_file, 'w', newline='') as f:
                if data['user_feedback']:
                    writer = csv.DictWriter(f, fieldnames=data['user_feedback'][0].keys())
                    writer.writeheader()
                    writer.writerows(data['user_feedback'])

        # App ratings CSV
        if data['app_ratings']:
            ratings_file = self.export_dir / f"app_ratings_{timestamp}.csv"
            with open(ratings_file, 'w', newline='') as f:
                if data['app_ratings']:
                    writer = csv.DictWriter(f, fieldnames=data['app_ratings'][0].keys())
                    writer.writeheader()
                    writer.writerows(data['app_ratings'])


def export_feedback():
    """CLI entry point for feedback export."""
    service = FeedbackService()
    result = service.export_feedback()

    print("Feedback Export Results:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    export_feedback()
