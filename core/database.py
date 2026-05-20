# database.py
# Stores every scan result in SQLite database
# So we can track risk history over time

import sqlite3
from datetime import datetime

DB_FILE = "debriswatch.db"

def init_db():
    """
    Create database tables if not exist
    Run this once when app starts
    """
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()

    # Table 1 — Every scan result
    c.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id          INTEGER PRIMARY KEY,
            scanned_at  TEXT,
            sat_name    TEXT,
            debris_name TEXT,
            risk_score  INTEGER,
            risk_label  TEXT,
            min_dist    REAL,
            min_hour    INTEGER
        )
    """)

    # Table 2 — Daily summary
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_summary (
            id           INTEGER PRIMARY KEY,
            date         TEXT,
            sat_name     TEXT,
            max_score    INTEGER,
            avg_score    REAL,
            total_high   INTEGER,
            total_medium INTEGER,
            total_safe   INTEGER
        )
    """)

    conn.commit()
    conn.close()
    print("  ✅ Database initialized")

def save_scan(satellites):
    """
    Save current scan results to database
    """
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()
    now  = datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    for sat in satellites:
        for d in sat["debris"]:
            c.execute("""
                INSERT INTO scans
                (scanned_at, sat_name, debris_name,
                 risk_score, risk_label,
                 min_dist, min_hour)
                VALUES (?,?,?,?,?,?,?)
            """, (
                now,
                sat["name"],
                d["name"],
                d["score"],
                d["label"],
                d["min_dist"],
                d["min_hour"],
            ))

    conn.commit()
    conn.close()

def get_history(sat_name, days=7):
    """
    Get risk score history for a satellite
    Returns list of (date, max_score) tuples
    """
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()

    c.execute("""
        SELECT
            DATE(scanned_at) as scan_date,
            MAX(risk_score)  as max_score,
            AVG(risk_score)  as avg_score,
            COUNT(*)         as total_scans
        FROM scans
        WHERE sat_name = ?
        AND scanned_at >= DATE('now', ?)
        GROUP BY DATE(scanned_at)
        ORDER BY scan_date ASC
    """, (sat_name, f"-{days} days"))

    rows = c.fetchall()
    conn.close()
    return rows

def get_all_history():
    """
    Get history for all satellites
    """
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()

    c.execute("""
        SELECT
            sat_name,
            DATE(scanned_at) as scan_date,
            MAX(risk_score)  as max_score
        FROM scans
        GROUP BY sat_name, DATE(scanned_at)
        ORDER BY scan_date ASC
    """)

    rows = c.fetchall()
    conn.close()
    return rows

def get_total_scans():
    """
    Total number of scans done so far
    """
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()
    c.execute("SELECT COUNT(*) FROM scans")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_highest_ever():
    """
    Highest risk score ever recorded
    """
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()
    c.execute("""
        SELECT sat_name, debris_name,
               risk_score, scanned_at
        FROM scans
        ORDER BY risk_score DESC
        LIMIT 1
    """)
    row = c.fetchone()
    conn.close()
    return row