#!/usr/bin/env python3
"""Pull CISA KEV JSON, upsert into SQLite, and print newly added CVEs."""

import argparse
import json
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
DEFAULT_DB = "cisa_kev.db"


def fetch_kev(url: str = KEV_URL, timeout: int = 30) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "kev-diff-script/1.0 (+local-threat-intel)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"[error] Failed to fetch/parse KEV feed: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict) or not isinstance(data.get("vulnerabilities"), list):
        print("[error] Unexpected KEV payload structure.", file=sys.stderr)
        sys.exit(1)
    return data


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS kev (
            cve_id TEXT PRIMARY KEY,
            vendor_project TEXT,
            product TEXT,
            vulnerability_name TEXT,
            date_added TEXT,
            due_date TEXT,
            ransomware_use TEXT,
            short_description TEXT,
            required_action TEXT,
            notes TEXT,
            first_seen_utc TEXT,
            last_seen_utc TEXT
        )
        """
    )
    conn.commit()
    return conn


def sync_kev(conn: sqlite3.Connection, payload: dict) -> list:
    now_utc = datetime.now(timezone.utc).isoformat()
    existing_ids = {
        row[0] for row in conn.execute("SELECT cve_id FROM kev").fetchall()
    }
    is_initial_seed = len(existing_ids) == 0

    new_entries = []
    for item in payload["vulnerabilities"]:
        cve_id = (item.get("cveID") or "").strip()
        if not cve_id:
            continue

        record = {
            "cve_id": cve_id,
            "vendor_project": item.get("vendorProject", ""),
            "product": item.get("product", ""),
            "vulnerability_name": item.get("vulnerabilityName", ""),
            "date_added": item.get("dateAdded", ""),
            "due_date": item.get("dueDate", ""),
            "ransomware_use": item.get("knownRansomwareCampaignUse", ""),
            "short_description": item.get("shortDescription", ""),
            "required_action": item.get("requiredAction", ""),
            "notes": item.get("notes", ""),
            "first_seen_utc": now_utc,
            "last_seen_utc": now_utc,
        }

        if cve_id not in existing_ids and not is_initial_seed:
            new_entries.append(record)

        conn.execute(
            """
            INSERT INTO kev (
                cve_id, vendor_project, product, vulnerability_name,
                date_added, due_date, ransomware_use, short_description,
                required_action, notes, first_seen_utc, last_seen_utc
            ) VALUES (
                :cve_id, :vendor_project, :product, :vulnerability_name,
                :date_added, :due_date, :ransomware_use, :short_description,
                :required_action, :notes, :first_seen_utc, :last_seen_utc
            )
            ON CONFLICT(cve_id) DO UPDATE SET
                vendor_project = excluded.vendor_project,
                product = excluded.product,
                vulnerability_name = excluded.vulnerability_name,
                date_added = excluded.date_added,
                due_date = excluded.due_date,
                ransomware_use = excluded.ransomware_use,
                short_description = excluded.short_description,
                required_action = excluded.required_action,
                notes = excluded.notes,
                last_seen_utc = excluded.last_seen_utc
            """,
            record,
        )

    conn.commit()
    return new_entries


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync CISA KEV into SQLite and show new CVEs.")
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to SQLite database")
    parser.add_argument("--url", default=KEV_URL, help="CISA KEV JSON feed URL")
    args = parser.parse_args()

    payload = fetch_kev(args.url)
    conn = init_db(args.db)
    try:
        new_entries = sync_kev(conn, payload)
        total_in_db = conn.execute("SELECT COUNT(*) FROM kev").fetchone()[0]
    finally:
        conn.close()

    version = payload.get("catalogVersion", "unknown")
    if not new_entries:
        print(f"CISA KEV ({version}) synced. 0 new CVEs since last run ({total_in_db} total).")
        return

    print(f"CISA KEV ({version}) — {len(new_entries)} new CVE(s) ({total_in_db} total):")
    for entry in new_entries:
        print(
            f"- {entry['cve_id']} | {entry['vendor_project']} — {entry['product']} "
            f"| added: {entry['date_added']} | due: {entry['due_date']} "
            f"| ransomware: {entry['ransomware_use']}\n"
            f"  {entry['vulnerability_name']}"
        )


if __name__ == "__main__":
    main()
