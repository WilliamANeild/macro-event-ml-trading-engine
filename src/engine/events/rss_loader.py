from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

import feedparser

logger = logging.getLogger(__name__)


# Default RSS feeds organized by category
DEFAULT_FEEDS: dict[str, str] = {
    # General news
    "https://apnews.com/index.rss": "apnews.com",
    "http://feeds.bbci.co.uk/news/world/rss.xml": "bbc.co.uk",
    "https://www.aljazeera.com/xml/rss/all.xml": "aljazeera.com",
    # Maritime / shipping
    "https://maritime-executive.com/feed": "maritime-executive.com",
    "https://gcaptain.com/feed/": "gcaptain.com",
    "https://splash247.com/feed/": "splash247.com",
    # Defense
    "https://www.defensenews.com/arc/outboundfeeds/rss/": "defensenews.com",
    # Central bank / macro
    "https://www.federalreserve.gov/feeds/press_all.xml": "federalreserve.gov",
}


@dataclass
class RSSEvent:
    """A normalized event record from an RSS feed entry."""
    title: str
    summary: str
    publish_date: date
    source_url: str
    source_domain: str
    raw_datetime: datetime | None = None


class RSSLoader:
    """Polls RSS feeds and extracts normalized event records.

    Deduplicates by URL to avoid processing the same article twice.
    """

    def __init__(
        self,
        feeds: dict[str, str] | None = None,
        max_age_days: int = 7,
    ) -> None:
        self._feeds = feeds or DEFAULT_FEEDS
        self._seen_urls: set[str] = set()
        self._max_age_days = max_age_days

    def load(self, as_of_date: date | None = None) -> list[RSSEvent]:
        """Poll all feeds and return deduplicated event records.

        Args:
            as_of_date: Only include entries published on or before this date.
                        Defaults to today.
        """
        if as_of_date is None:
            as_of_date = date.today()

        all_events: list[RSSEvent] = []

        for feed_url, domain in self._feeds.items():
            try:
                events = self._parse_feed(feed_url, domain, as_of_date)
                all_events.extend(events)
            except Exception:
                logger.warning("Failed to parse feed: %s", feed_url, exc_info=True)

        return all_events

    def _parse_feed(
        self, feed_url: str, domain: str, as_of_date: date
    ) -> list[RSSEvent]:
        """Parse a single RSS feed and return new (unseen) events."""
        feed = feedparser.parse(feed_url)
        events: list[RSSEvent] = []

        for entry in feed.entries:
            url = getattr(entry, "link", "") or ""

            # Deduplicate by URL
            if url in self._seen_urls:
                continue

            # Parse publish date
            pub_dt = _parse_entry_date(entry)
            if pub_dt is None:
                pub_date = as_of_date
            else:
                pub_date = pub_dt.date()

            # Skip entries older than max_age_days
            age = (as_of_date - pub_date).days
            if age > self._max_age_days or age < 0:
                continue

            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""

            # Derive domain from URL if not provided
            source_domain = domain
            if not source_domain and url:
                parsed = urlparse(url)
                source_domain = parsed.netloc

            if url:
                self._seen_urls.add(url)

            events.append(RSSEvent(
                title=title,
                summary=summary,
                publish_date=pub_date,
                source_url=url,
                source_domain=source_domain,
                raw_datetime=pub_dt,
            ))

        logger.info(
            "Parsed %d new entries from %s (%s)", len(events), domain, feed_url
        )
        return events

    def clear_seen(self) -> None:
        """Reset the deduplication set (e.g., between backtest periods)."""
        self._seen_urls.clear()

    @property
    def seen_count(self) -> int:
        return len(self._seen_urls)


def _parse_entry_date(entry: Any) -> datetime | None:
    """Try to parse the publish date from an RSS feed entry."""
    # feedparser provides 'published_parsed' as a time.struct_time
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            import calendar
            ts = calendar.timegm(entry.published_parsed)
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (ValueError, OverflowError):
            pass

    # Try the raw string
    for field_name in ("published", "updated"):
        raw = getattr(entry, field_name, None)
        if raw:
            try:
                return parsedate_to_datetime(raw)
            except (ValueError, TypeError):
                pass

    return None
