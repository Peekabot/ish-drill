#!/usr/bin/env python3
"""Pull FBI national & field-office RSS feeds, store in SQLite, and print new items."""

import argparse
import sqlite3
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

DEFAULT_FEEDS = {
    "national": "https://www.fbi.gov/news/press-releases/RSS",
    "albany": "https://www.fbi.gov/feeds/albany-news/RSS",
    "newyork": "https://www.fbi.gov/contact-us/field-offices/newyork/news/press-releases/RSS",
    "boston": "https://www.fbi.gov/contact-us/field-offices/boston/news/press-releases/RSS",
}
DEFAULT_DB = "fbi_rss.db"


def fetch_xml(url: str, timeout: int = 30) -> ET.Element:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "fbi-rss-diff/1.0 (+local-threat-intel)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return ET.fromstring(raw)


def parse_rss_items(root: ET.Element, source_name: str, feed_url: str) -> list:
    items = []
    candidates = root.findall(".//item")
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    if not candidates:
        candidates = root.findall(".//atom:entry", ns)

    for node in candidates:
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        if not link:
            link_el = node.find("atom:link", ns)
            if link_el is not None:
                link = (link_el.attrib.get("href") or "").strip()

        guid = (node.findtext("guid") or node.findtext("id") or link or title).strip()
        pub_date = (
            node.findtext("pubDate")
            or node.findtext("updated")
            or node.findtext("published")
            or ""
        ).strip()

        if not guid and not title:
            continue

        items.append(
            {
                "item_id": f"{source_name}:{guid}",
                "source": source_name,
                "feed_url": feed_url,
                "title": title,
                "link": link,
                "published": pub_date,
            }
        )
    return items


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fbi_items (
            item_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            feed_url TEXT NOT NULL,
            title TEXT,
            link TEXT,
            published TEXT,
            first_seen_utc TEXT NOT NULL,
            last_seen_utc TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def sync_feed(conn: sqlite3.Connection, source_name: str, feed_url: str):
    now_utc = datetime.now(timezone.utc).isoformat()
    existing_count = conn.execute(
        "SELECT COUNT(*) FROM fbi_items WHERE source = ?", (source_name,)
    ).fetchone()[0]
    is_initial_seed = existing_count == 0

    existing_ids = {
        row[0]
        for row in conn.execute(
            "SELECT item_id FROM fbi_items WHERE source = ?", (source_name,)
        ).fetchall()
    }

    root = fetch_xml(feed_url)
    parsed = parse_rss_items(root, source_name, feed_url)

    new_items = []
    for item in parsed:
        if item["item_id"] not in existing_ids and not is_initial_seed:
            new_items.append(item)

        conn.execute(
            """
            INSERT INTO fbi_items (
                item_id, source, feed_url, title, link, published,
                first_seen_utc, last_seen_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                title = excluded.title,
                link = excluded.link,
                published = excluded.published,
                last_seen_utc = excluded.last_seen_utc
            """,
            (
                item["item_id"],
                item["source"],
                item["feed_url"],
                item["title"],
                item["link"],
                item["published"],
                now_utc,
                now_utc,
            ),
        )

    conn.commit()
    return new_items, is_initial_seed


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync FBI RSS feeds to SQLite and print new items.")
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to SQLite database")
    parser.add_argument(
        "--offices",
        nargs="*",
        default=["albany", "newyork", "boston"],
        help="Field office slugs to include alongside national (e.g. albany newyork boston)",
    )
    parser.add_argument(
        "--national-only",
        action="store_true",
        help="Only pull the national FBI press release RSS feed",
    )
    args = parser.parse_args()

    feeds = {"national": DEFAULT_FEEDS["national"]}
    if not args.national_only:
        for slug in args.offices:
            clean = slug.strip().lower()
            if not clean:
                continue
            # Prefer known working feeds; fall back to common patterns
            if clean in DEFAULT_FEEDS:
                feeds[clean] = DEFAULT_FEEDS[clean]
            else:
                # Try the /feeds/{slug}-news/RSS pattern first (more reliable for many offices)
                feeds[clean] = f"https://www.fbi.gov/feeds/{clean}-news/RSS"

    conn = init_db(args.db)
    all_new = []
    try:
        for name, url in feeds.items():
            try:
                new_items, seeded = sync_feed(conn, name, url)
                if seeded:
                    print(f"[{name}] seeded initial items into {args.db}")
                else:
                    all_new.extend(new_items)
            except (urllib.error.URLError, TimeoutError, ET.ParseError, OSError) as exc:
                print(f"[warn] Failed to sync {name} ({url}): {exc}", file=sys.stderr)
    finally:
        conn.close()

    if not all_new:
        print("No new FBI RSS items since last run.")
        return

    print(f"Found {len(all_new)} new FBI item(s):")
    for item in all_new:
        print(f"- [{item['source']}] {item['title']} ({item['published']})\n  {item['link']}")


if __name__ == "__main__":
    main()
