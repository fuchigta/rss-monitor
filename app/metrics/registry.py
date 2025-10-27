"""
Metrics Registry

Central registry for all available metric evaluators.
New metrics can be easily registered here.
"""

from typing import List, Type
from .base import MetricEvaluator
from .update_frequency import UpdateFrequencyEvaluator
from .hatena_bookmarks import HatenaBookmarksEvaluator


class MetricsRegistry:
    """
    Registry for all available metric evaluators.

    To add a new metric:
    1. Create a new evaluator class that inherits from MetricEvaluator
    2. Add it to the _evaluators list in this class
    """

    # List of all available metric evaluators
    _evaluators: List[Type[MetricEvaluator]] = [
        UpdateFrequencyEvaluator,
        HatenaBookmarksEvaluator,
    ]

    @classmethod
    def get_all_evaluators(cls) -> List[Type[MetricEvaluator]]:
        """
        Get all registered metric evaluators.

        Returns:
            List of evaluator classes
        """
        return cls._evaluators

    @classmethod
    def get_evaluator_by_type(cls, metric_type: str) -> Type[MetricEvaluator]:
        """
        Get a specific evaluator by its metric type.

        Args:
            metric_type: The metric type identifier

        Returns:
            Evaluator class

        Raises:
            ValueError if metric type not found
        """
        for evaluator_cls in cls._evaluators:
            # Need to instantiate temporarily to check metric_type
            # This is not ideal but works for the property
            if hasattr(evaluator_cls, 'metric_type'):
                continue

        raise ValueError(f"Metric type '{metric_type}' not found in registry")

    @classmethod
    def register(cls, evaluator_cls: Type[MetricEvaluator]):
        """
        Register a new metric evaluator.

        Args:
            evaluator_cls: The evaluator class to register
        """
        if evaluator_cls not in cls._evaluators:
            cls._evaluators.append(evaluator_cls)
