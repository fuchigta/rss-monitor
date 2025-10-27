"""
Main application entry point for RSS Monitor.

This script can be run with different commands:
- collect: Collect RSS feeds
- update-bookmarks: Update Hatena bookmark counts
- evaluate-metrics: Evaluate all metrics
- run-all: Run all tasks in sequence
"""

import sys
import logging
from database import get_db_connection, close_db_connection
from feed_collector import FeedCollector
from hatena_client import HatenaBookmarkClient
from metrics.registry import MetricsRegistry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_feeds(db_conn):
    """
    Collect all active RSS feeds.

    Args:
        db_conn: Database connection
    """
    logger.info("Starting feed collection...")
    collector = FeedCollector(db_conn)
    collector.collect_all_active_feeds()
    logger.info("Feed collection completed")


def update_bookmarks(db_conn):
    """
    Update Hatena bookmark counts for recent entries.

    Args:
        db_conn: Database connection
    """
    logger.info("Starting bookmark count updates...")
    client = HatenaBookmarkClient(db_conn)
    client.update_all_recent_entries(days=7)
    logger.info("Bookmark count updates completed")


def evaluate_metrics(db_conn):
    """
    Evaluate all registered metrics for all feeds.

    Args:
        db_conn: Database connection
    """
    logger.info("Starting metrics evaluation...")

    # Get all active feeds
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, name FROM feeds WHERE active = TRUE")
    feeds = cursor.fetchall()
    cursor.close()

    logger.info(f"Evaluating metrics for {len(feeds)} feeds")

    # Get all registered metric evaluators
    evaluator_classes = MetricsRegistry.get_all_evaluators()

    for feed_id, feed_name in feeds:
        logger.info(f"Evaluating metrics for feed: {feed_name} (ID: {feed_id})")

        for evaluator_cls in evaluator_classes:
            evaluator = evaluator_cls(db_conn)
            logger.info(f"  Running evaluator: {evaluator.metric_name}")

            try:
                result = evaluator.evaluate(feed_id)

                if result is not None:
                    value = result['value']
                    metadata = result.get('metadata')

                    # Save metric
                    evaluator.save_metric(feed_id, value, metadata)

                    # Check alerts
                    evaluator.check_alerts(feed_id, value)

                    logger.info(f"    Result: {value:.2f}")
                else:
                    logger.warning(f"    No result for {evaluator.metric_name}")
            except Exception as e:
                logger.error(f"    Error evaluating {evaluator.metric_name}: {str(e)}")

    logger.info("Metrics evaluation completed")


def run_all(db_conn):
    """
    Run all tasks in sequence.

    Args:
        db_conn: Database connection
    """
    logger.info("Running all tasks...")
    collect_feeds(db_conn)
    update_bookmarks(db_conn)
    evaluate_metrics(db_conn)
    logger.info("All tasks completed")


def main():
    """
    Main application entry point.
    """
    if len(sys.argv) < 2:
        print("Usage: python main.py [collect|update-bookmarks|evaluate-metrics|run-all]")
        sys.exit(1)

    command = sys.argv[1]

    # Connect to database
    db_conn = None
    try:
        db_conn = get_db_connection()

        # Execute command
        if command == 'collect':
            collect_feeds(db_conn)
        elif command == 'update-bookmarks':
            update_bookmarks(db_conn)
        elif command == 'evaluate-metrics':
            evaluate_metrics(db_conn)
        elif command == 'run-all':
            run_all(db_conn)
        else:
            logger.error(f"Unknown command: {command}")
            print("Valid commands: collect, update-bookmarks, evaluate-metrics, run-all")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)
    finally:
        if db_conn:
            close_db_connection(db_conn)


if __name__ == '__main__':
    main()
