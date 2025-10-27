"""
Hatena Bookmark API Client

Fetches bookmark counts from Hatena Bookmark API.
"""

import requests
import time
import logging
from typing import Optional, List, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HatenaBookmarkClient:
    """
    Client for Hatena Bookmark API.
    """

    HATENA_API_URL = "https://bookmark.hatenaapis.com/count/entry"
    REQUEST_DELAY = 0.5  # Delay between requests to avoid rate limiting

    def __init__(self, db_connection):
        """
        Initialize the Hatena Bookmark client.

        Args:
            db_connection: Database connection object
        """
        self.db = db_connection
        self.session = requests.Session()

    def update_all_recent_entries(self, days: int = 7):
        """
        Update bookmark counts for all recent entries.

        Args:
            days: Number of days to look back for entries
        """
        cursor = self.db.cursor()

        cursor.execute("""
            SELECT id, link
            FROM entries
            WHERE first_seen_at >= NOW() - INTERVAL '%s days'
            AND link IS NOT NULL
            AND link != ''
            ORDER BY first_seen_at DESC
        """, (days,))

        entries = cursor.fetchall()
        cursor.close()

        logger.info(f"Found {len(entries)} recent entries to update bookmark counts")

        for entry_id, link in entries:
            try:
                count = self.get_bookmark_count(link)
                if count is not None:
                    self._store_bookmark_count(entry_id, count)
                time.sleep(self.REQUEST_DELAY)
            except Exception as e:
                logger.error(f"Error updating bookmark count for entry {entry_id}: {str(e)}")

    def get_bookmark_count(self, url: str) -> Optional[int]:
        """
        Get bookmark count for a specific URL.

        Args:
            url: The URL to check

        Returns:
            Bookmark count or None if failed
        """
        try:
            response = self.session.get(
                self.HATENA_API_URL,
                params={'url': url},
                timeout=10
            )

            if response.status_code == 200:
                try:
                    count = int(response.text.strip())
                    return count
                except ValueError:
                    logger.warning(f"Invalid response for {url}: {response.text}")
                    return 0
            else:
                logger.warning(f"Failed to get bookmark count for {url}: {response.status_code}")
                return None
        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {str(e)}")
            return None

    def get_bookmark_counts_batch(self, urls: List[str]) -> List[Tuple[str, Optional[int]]]:
        """
        Get bookmark counts for multiple URLs.

        Args:
            urls: List of URLs to check

        Returns:
            List of (url, count) tuples
        """
        results = []
        for url in urls:
            count = self.get_bookmark_count(url)
            results.append((url, count))
            time.sleep(self.REQUEST_DELAY)
        return results

    def _store_bookmark_count(self, entry_id: int, count: int):
        """
        Store bookmark count in the database.

        Args:
            entry_id: The entry ID
            count: The bookmark count
        """
        cursor = self.db.cursor()

        try:
            cursor.execute("""
                INSERT INTO hatena_bookmarks (entry_id, bookmark_count, checked_at)
                VALUES (%s, %s, %s)
            """, (entry_id, count, datetime.now()))

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing bookmark count: {str(e)}")
        finally:
            cursor.close()
