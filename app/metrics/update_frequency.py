"""
Update Frequency Metric Evaluator

Calculates how frequently a feed is updated (entries per hour in the last 24 hours).
"""

from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from .base import MetricEvaluator


class UpdateFrequencyEvaluator(MetricEvaluator):
    """
    Evaluates the update frequency of a feed.

    Measures entries per hour over the last 24 hours.
    """

    @property
    def metric_type(self) -> str:
        return 'update_frequency'

    @property
    def metric_name(self) -> str:
        return 'Update Frequency (entries/hour)'

    def evaluate(self, feed_id: int) -> Optional[Dict[str, Any]]:
        """
        Calculate update frequency for a feed.

        Args:
            feed_id: The feed ID to evaluate

        Returns:
            Dictionary with value (entries per hour) and metadata
        """
        cursor = self.db.cursor()

        # Calculate entries in the last 24 hours
        time_window = datetime.now() - timedelta(hours=24)

        cursor.execute("""
            SELECT COUNT(*) as entry_count
            FROM entries
            WHERE feed_id = %s
            AND first_seen_at >= %s
        """, (feed_id, time_window))

        result = cursor.fetchone()
        cursor.close()

        if result is None:
            return None

        entry_count = result[0]
        entries_per_hour = entry_count / 24.0

        metadata = {
            'time_window_hours': 24,
            'total_entries': entry_count,
            'measured_at': datetime.now().isoformat()
        }

        return {
            'value': entries_per_hour,
            'metadata': metadata
        }
