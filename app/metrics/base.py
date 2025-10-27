"""
Base class for metrics evaluators.
This provides a plugin architecture for adding new metrics.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime


class MetricEvaluator(ABC):
    """
    Base class for all metric evaluators.

    Each metric evaluator should:
    1. Inherit from this class
    2. Implement the evaluate() method
    3. Return a metric value and optional metadata
    """

    def __init__(self, db_connection):
        """
        Initialize the metric evaluator.

        Args:
            db_connection: Database connection object
        """
        self.db = db_connection

    @property
    @abstractmethod
    def metric_type(self) -> str:
        """
        Unique identifier for this metric type.

        Returns:
            String identifier (e.g., 'update_frequency', 'avg_hatena_bookmarks')
        """
        pass

    @property
    @abstractmethod
    def metric_name(self) -> str:
        """
        Human-readable name for this metric.

        Returns:
            Display name for the metric
        """
        pass

    @abstractmethod
    def evaluate(self, feed_id: int) -> Optional[Dict[str, Any]]:
        """
        Evaluate the metric for a given feed.

        Args:
            feed_id: The feed ID to evaluate

        Returns:
            Dictionary containing:
                - value: The metric value (numeric)
                - metadata: Optional dict with additional information
            Returns None if metric cannot be calculated
        """
        pass

    def save_metric(self, feed_id: int, value: float, metadata: Optional[Dict] = None):
        """
        Save a metric value to the database.

        Args:
            feed_id: The feed ID
            value: The metric value
            metadata: Optional metadata dict
        """
        import json
        cursor = self.db.cursor()

        metadata_json = json.dumps(metadata) if metadata else None

        cursor.execute("""
            INSERT INTO metrics (feed_id, metric_type, metric_value, metadata, measured_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (feed_id, self.metric_type, value, metadata_json, datetime.now()))

        self.db.commit()
        cursor.close()

    def check_alerts(self, feed_id: int, value: float):
        """
        Check if any alert rules are triggered for this metric.

        Args:
            feed_id: The feed ID
            value: The current metric value
        """
        cursor = self.db.cursor()

        # Get all active alert rules for this feed and metric type
        cursor.execute("""
            SELECT id, rule_name, condition, threshold
            FROM alert_rules
            WHERE feed_id = %s
            AND metric_type = %s
            AND enabled = TRUE
        """, (feed_id, self.metric_type))

        rules = cursor.fetchall()

        for rule_id, rule_name, condition, threshold in rules:
            triggered = self._evaluate_condition(value, condition, threshold)

            if triggered:
                # Check if there's already an unresolved alert
                cursor.execute("""
                    SELECT id FROM alerts
                    WHERE alert_rule_id = %s
                    AND resolved = FALSE
                    ORDER BY triggered_at DESC
                    LIMIT 1
                """, (rule_id,))

                existing_alert = cursor.fetchone()

                if not existing_alert:
                    # Create new alert
                    message = f"{rule_name}: {self.metric_name} is {value:.2f} (threshold: {threshold:.2f})"
                    cursor.execute("""
                        INSERT INTO alerts
                        (alert_rule_id, feed_id, metric_type, metric_value, threshold, message, severity)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (rule_id, feed_id, self.metric_type, value, threshold, message, 'warning'))
            else:
                # Resolve any existing alerts if condition is no longer met
                cursor.execute("""
                    UPDATE alerts
                    SET resolved = TRUE, resolved_at = %s
                    WHERE alert_rule_id = %s
                    AND resolved = FALSE
                """, (datetime.now(), rule_id))

        self.db.commit()
        cursor.close()

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """
        Evaluate an alert condition.

        Args:
            value: Current metric value
            condition: Condition type ('lt', 'gt', 'eq', 'lte', 'gte')
            threshold: Threshold value

        Returns:
            True if condition is met, False otherwise
        """
        conditions = {
            'lt': lambda v, t: v < t,
            'lte': lambda v, t: v <= t,
            'gt': lambda v, t: v > t,
            'gte': lambda v, t: v >= t,
            'eq': lambda v, t: abs(v - t) < 0.001,
        }

        return conditions.get(condition, lambda v, t: False)(value, threshold)
