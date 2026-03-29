"""
MargMitra - Database Layer
Handles SQLite storage for all scan results.
"""

import sqlite3
from datetime import datetime

DB_PATH = "margmitra.db"


def init_db():
    """Create tables if they don't exist. Call once on startup."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            original    TEXT    NOT NULL,
            transliterated TEXT NOT NULL,
            target_lang TEXT    NOT NULL DEFAULT 'hi',
            image_name  TEXT,
            scanned_at  TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] Database ready.")


def save_scan(original: str, transliterated: str, target_lang: str, image_name: str = None) -> int:
    """Save one scan result. Returns the new row ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO scans (original, transliterated, target_lang, image_name, scanned_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (original, transliterated, target_lang, image_name, datetime.now().isoformat())
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    print(f"[DB] Saved scan #{new_id}: '{original}' → '{transliterated}'")
    return new_id


def get_all_scans() -> list[dict]:
    """Return all scans, newest first."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scans ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_scan_by_id(scan_id: int) -> dict | None:
    """Return a single scan by ID, or None if not found."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_scan(scan_id: int) -> bool:
    """Delete a scan by ID. Returns True if deleted, False if not found."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_stats() -> dict:
    """Return summary stats for the home screen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM scans")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT target_lang) FROM scans")
    langs = cursor.fetchone()[0]
    conn.close()
    return {"total_scans": total, "languages_used": langs}
