"""
Hatena Bookmarks Metric Evaluator

Calculates average Hatena bookmark count for recent entries.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from .base import MetricEvaluator


class HatenaBookmarksEvaluator(MetricEvaluator):
    """
    Evaluates average Hatena bookmark count for a feed.

    Calculates the average bookmark count for entries in the last 7 days.
    """

    @property
    def metric_type(self) -> str:
        return 'avg_hatena_bookmarks'

    @property
    def metric_name(self) -> str:
        return 'Average Hatena Bookmarks'

    def evaluate(self, feed_id: int) -> Optional[Dict[str, Any]]:
        """
        Calculate average Hatena bookmark count for recent entries.

        Args:
            feed_id: The feed ID to evaluate

        Returns:
            Dictionary with average bookmark count and metadata
        """
        cursor = self.db.cursor()

        # Get entries from the last 7 days
        time_window = datetime.now() - timedelta(days=7)

        cursor.execute("""
            SELECT
                COUNT(DISTINCT e.id) as entry_count,
                COALESCE(AVG(hb.bookmark_count), 0) as avg_bookmarks,
                COALESCE(SUM(hb.bookmark_count), 0) as total_bookmarks
            FROM entries e
            LEFT JOIN (
                SELECT DISTINCT ON (entry_id)
                    entry_id,
                    bookmark_count,
                    checked_at
                FROM hatena_bookmarks
                ORDER BY entry_id, checked_at DESC
            ) hb ON e.id = hb.entry_id
            WHERE e.feed_id = %s
            AND e.first_seen_at >= %s
        """, (feed_id, time_window))

        result = cursor.fetchone()
        cursor.close()

        if result is None or result[0] == 0:
            return None

        entry_count, avg_bookmarks, total_bookmarks = result

        metadata = {
            'time_window_days': 7,
            'total_entries': entry_count,
            'total_bookmarks': int(total_bookmarks),
            'measured_at': datetime.now().isoformat()
        }

        return {
            'value': float(avg_bookmarks),
            'metadata': metadata
        }
