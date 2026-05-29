# database.py
# Database for DebrisWatch AI
# Now includes Conjunction Event Log

import sqlite3
from datetime import datetime

DB_FILE = "debriswatch.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()

    # Table 1 — Scan results
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
        CREATE TABLE IF NOT EXISTS
        daily_summary (
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

    # Table 3 — Conjunction Event Log
    # NEW — mirrors ISRO SSA Centre work
    c.execute("""
        CREATE TABLE IF NOT EXISTS
        conjunction_events (
            id           INTEGER PRIMARY KEY,
            logged_at    TEXT,
            sat_name     TEXT,
            debris_name  TEXT,
            distance_km  REAL,
            tca_hour     INTEGER,
            ml_prob      REAL,
            risk_level   TEXT,
            maneuver_needed INTEGER,
            delta_v_ms   REAL,
            fuel_kg      REAL,
            resolved     INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    print("  ✅ Database initialized")

def save_scan(satellites):
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()
    now  = datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    for sat in satellites:
        for d in sat["debris"]:
            c.execute("""
                INSERT INTO scans
                (scanned_at, sat_name,
                 debris_name, risk_score,
                 risk_label, min_dist,
                 min_hour)
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

def log_conjunction_event(
    sat_name, debris_name,
    distance_km, tca_hour,
    ml_prob, risk_level,
    maneuver_needed=False,
    delta_v_ms=0.0,
    fuel_kg=0.0
):
    """
    Log a conjunction event
    Called whenever debris comes
    within 5000 km of a satellite

    This mirrors what ISRO SSA
    Control Centre logs daily
    """
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()
    now  = datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # Check if same event already logged
    # today — avoid duplicates
    c.execute("""
        SELECT id FROM conjunction_events
        WHERE sat_name = ?
        AND debris_name = ?
        AND DATE(logged_at) = DATE('now')
    """, (sat_name, debris_name))

    existing = c.fetchone()

    if not existing:
        c.execute("""
            INSERT INTO conjunction_events
            (logged_at, sat_name, debris_name,
             distance_km, tca_hour, ml_prob,
             risk_level, maneuver_needed,
             delta_v_ms, fuel_kg)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            now, sat_name, debris_name,
            distance_km, tca_hour,
            ml_prob, risk_level,
            1 if maneuver_needed else 0,
            delta_v_ms, fuel_kg
        ))
        conn.commit()

    conn.close()

def get_conjunction_events(days=7):
    """
    Get all conjunction events
    from last N days
    """
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()

    c.execute("""
        SELECT
            logged_at, sat_name,
            debris_name, distance_km,
            tca_hour, ml_prob,
            risk_level, maneuver_needed,
            delta_v_ms, fuel_kg
        FROM conjunction_events
        WHERE logged_at >=
              DATE('now', ?)
        ORDER BY logged_at DESC
    """, (f"-{days} days",))

    rows = c.fetchall()
    conn.close()
    return rows

def get_conjunction_stats():
    """
    Summary statistics of
    conjunction events
    Like ISRO's weekly SSA report
    """
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()

    # Total events this week
    c.execute("""
        SELECT COUNT(*)
        FROM conjunction_events
        WHERE logged_at >=
              DATE('now', '-7 days')
    """)
    total_week = c.fetchone()[0]

    # Events needing maneuver
    c.execute("""
        SELECT COUNT(*)
        FROM conjunction_events
        WHERE maneuver_needed = 1
        AND logged_at >=
            DATE('now', '-7 days')
    """)
    maneuver_week = c.fetchone()[0]

    # Total events all time
    c.execute("""
        SELECT COUNT(*)
        FROM conjunction_events
    """)
    total_all = c.fetchone()[0]

    # Events by satellite this week
    c.execute("""
        SELECT sat_name, COUNT(*) as cnt
        FROM conjunction_events
        WHERE logged_at >=
              DATE('now', '-7 days')
        GROUP BY sat_name
        ORDER BY cnt DESC
    """)
    by_satellite = c.fetchall()

    # Daily event count (last 7 days)
    c.execute("""
        SELECT
            DATE(logged_at) as evt_date,
            COUNT(*) as cnt,
            SUM(maneuver_needed) as maneuvers
        FROM conjunction_events
        WHERE logged_at >=
              DATE('now', '-7 days')
        GROUP BY DATE(logged_at)
        ORDER BY evt_date ASC
    """)
    daily = c.fetchall()

    # Closest approach ever logged
    c.execute("""
        SELECT sat_name, debris_name,
               distance_km, logged_at
        FROM conjunction_events
        ORDER BY distance_km ASC
        LIMIT 1
    """)
    closest_ever = c.fetchone()

    conn.close()

    return {
        "total_week":    total_week,
        "maneuver_week": maneuver_week,
        "total_all":     total_all,
        "by_satellite":  by_satellite,
        "daily":         daily,
        "closest_ever":  closest_ever,
    }

def get_history(sat_name, days=7):
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
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()
    c.execute("""
        SELECT
            sat_name,
            DATE(scanned_at) as scan_date,
            MAX(risk_score)  as max_score
        FROM scans
        GROUP BY sat_name,
                 DATE(scanned_at)
        ORDER BY scan_date ASC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def get_total_scans():
    conn = sqlite3.connect(DB_FILE)
    c    = conn.cursor()
    c.execute("SELECT COUNT(*) FROM scans")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_highest_ever():
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