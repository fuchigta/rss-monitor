"""
RSS Feed Collector

Fetches and parses RSS/Atom feeds and stores entries in the database.
"""

import feedparser
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from dateutil import parser as date_parser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeedCollector:
    """
    Collects and processes RSS/Atom feeds.
    """

    def __init__(self, db_connection):
        """
        Initialize the feed collector.

        Args:
            db_connection: Database connection object
        """
        self.db = db_connection

    def collect_all_active_feeds(self):
        """
        Collect all active feeds from the database.
        """
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, name, url
            FROM feeds
            WHERE active = TRUE
        """)

        feeds = cursor.fetchall()
        cursor.close()

        logger.info(f"Found {len(feeds)} active feeds to collect")

        for feed_id, feed_name, feed_url in feeds:
            logger.info(f"Collecting feed: {feed_name} ({feed_url})")
            try:
                self.collect_feed(feed_id, feed_url)
            except Exception as e:
                logger.error(f"Error collecting feed {feed_name}: {str(e)}")

    def collect_feed(self, feed_id: int, feed_url: str):
        """
        Collect a single feed and store its entries.

        Args:
            feed_id: The feed ID
            feed_url: The feed URL
        """
        # Parse the feed
        feed = feedparser.parse(feed_url)

        if feed.bozo:
            logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")

        # Process each entry
        new_entries = 0
        for entry in feed.entries:
            if self._store_entry(feed_id, entry):
                new_entries += 1

        logger.info(f"Stored {new_entries} new entries for feed {feed_id}")

    def _store_entry(self, feed_id: int, entry: Any) -> bool:
        """
        Store a single feed entry in the database.

        Args:
            feed_id: The feed ID
            entry: Feed entry object from feedparser

        Returns:
            True if new entry was stored, False if already exists
        """
        cursor = self.db.cursor()

        # Extract entry data
        entry_id = entry.get('id', entry.get('link', ''))
        title = entry.get('title', '')
        link = entry.get('link', '')
        author = entry.get('author', '')
        summary = entry.get('summary', '')
        content = ''

        # Get content if available
        if hasattr(entry, 'content'):
            content = entry.content[0].value if entry.content else ''

        # Parse published date
        published_at = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6])
            except:
                pass

        if not published_at and hasattr(entry, 'published'):
            try:
                published_at = date_parser.parse(entry.published)
            except:
                pass

        # Try to insert the entry
        try:
            cursor.execute("""
                INSERT INTO entries
                (feed_id, entry_id, title, link, published_at, author, summary, content)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (feed_id, entry_id) DO NOTHING
                RETURNING id
            """, (feed_id, entry_id, title, link, published_at, author, summary, content))

            result = cursor.fetchone()
            self.db.commit()
            cursor.close()

            return result is not None
        except Exception as e:
            self.db.rollback()
            cursor.close()
            logger.error(f"Error storing entry: {str(e)}")
            return False
