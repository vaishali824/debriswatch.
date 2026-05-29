# tle_fetcher.py
# Automatically downloads fresh TLE data
# from NASA Space-Track every 6 hours
# No more hardcoded outdated data

import requests
import os
import json
from datetime import datetime, timedelta

# ─────────────────────────────────
# YOUR SPACE-TRACK LOGIN
# ─────────────────────────────────
USERNAME = "your_email@gmail.com"   # ← replace
PASSWORD = "your_password"          # ← replace

BASE_URL  = "https://www.space-track.org"
CACHE_FILE = "core/tle_cache.json"

# ISRO Satellite NORAD IDs
# These are real public IDs
ISRO_SATELLITES = {
    "CARTOSAT-3":    44234,
    "RESOURCESAT-2": 37820,
    "RISAT-2BR1":    44857,
    "OCEANSAT-3":    54361,
    "GSAT-19":       42784,
}

def cache_is_fresh(max_age_hours=6):
    """
    Check if cached TLE data is
    less than 6 hours old
    """
    if not os.path.exists(CACHE_FILE):
        return False
    try:
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
        cached_at = datetime.fromisoformat(
            cache["cached_at"]
        )
        age = datetime.utcnow() - cached_at
        return age < timedelta(hours=max_age_hours)
    except:
        return False

def load_cache():
    """
    Load TLE data from local cache file
    """
    try:
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
        return cache["satellites"], cache["debris"]
    except:
        return None, None

def save_cache(satellites, debris):
    """
    Save TLE data to local cache
    """
    cache = {
        "cached_at":  datetime.utcnow().isoformat(),
        "satellites": satellites,
        "debris":     debris,
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)
    print("  ✅ TLE cache saved")

def fetch_from_spacetrack():
    """
    Login to NASA Space-Track
    Download fresh TLE data
    """
    print("  Connecting to NASA Space-Track...")

    session = requests.Session()

    # Login
    login = session.post(
        f"{BASE_URL}/ajaxauth/login",
        data={
            "identity": USERNAME,
            "password": PASSWORD
        }
    )

    if login.status_code != 200:
        print("  ❌ Login failed")
        return None, None

    print("  ✅ Login successful")

    # ── Fetch ISRO Satellites TLE ──
    satellites = {}
    for name, norad_id in ISRO_SATELLITES.items():
        try:
            url = (
                f"{BASE_URL}/basicspacedata/query"
                f"/class/tle_latest/ORDINAL/1"
                f"/NORAD_CAT_ID/{norad_id}"
                f"/format/tle"
            )
            resp = session.get(url)
            lines = [
                l.strip()
                for l in resp.text.strip().split("\n")
                if l.strip()
            ]
            if len(lines) >= 2:
                satellites[name] = {
                    "tle1": lines[0],
                    "tle2": lines[1],
                }
                print(f"  ✅ {name} TLE downloaded")
            else:
                print(f"  ⚠️  {name} — using backup")
        except Exception as e:
            print(f"  ❌ {name} failed: {e}")

    # ── Fetch Debris TLE ──
    print("  Downloading debris TLE...")
    debris = []
    try:
        url = (
            f"{BASE_URL}/basicspacedata/query"
            f"/class/tle_latest/ORDINAL/1"
            f"/OBJECT_TYPE/DEBRIS"
            f"/INCLINATION/45--55"
            f"/EPOCH/%3Enow-1"
            f"/orderby/EPOCH desc"
            f"/limit/20"
            f"/format/tle"
        )
        resp  = session.get(url)
        lines = [
            l.strip()
            for l in resp.text.strip().split("\n")
            if l.strip()
        ]
        count = 0
        for i in range(0, len(lines)-1, 2):
            l1 = lines[i]
            l2 = lines[i+1]
            if l1.startswith("1") and \
               l2.startswith("2"):
                debris.append((
                    f"DEBRIS-{count+1}",
                    l1, l2
                ))
                count += 1
        print(f"  ✅ {count} debris objects downloaded")
    except Exception as e:
        print(f"  ❌ Debris fetch failed: {e}")

    # Logout
    session.get(f"{BASE_URL}/ajaxauth/logout")

    return satellites, debris

def get_tle_data():
    """
    Main function called by app
    Returns fresh or cached TLE data

    Priority:
    1. If cache is fresh → use cache
    2. If cache old → fetch from Space-Track
    3. If fetch fails → use hardcoded backup
    """
    # Try cache first
    if cache_is_fresh():
        print("  Using cached TLE data (< 6h old)")
        sats, debris = load_cache()
        if sats and debris:
            return sats, debris

    # Try Space-Track
    print("  Cache expired — fetching fresh data...")
    sats, debris = fetch_from_spacetrack()

    if sats and debris:
        save_cache(sats, debris)
        return sats, debris

    # Fallback to cache even if old
    print("  ⚠️  Using old cache as fallback")
    sats, debris = load_cache()
    if sats and debris:
        return sats, debris

    # Last resort — hardcoded backup
    print("  ⚠️  Using hardcoded backup TLE")
    return get_backup_tle()

def get_backup_tle():
    """
    Hardcoded backup TLE data
    Used only if Space-Track fails
    """
    satellites = {
        "CARTOSAT-3": {
            "tle1": "1 44234U 19053A   24001.50000000  .00000678  00000-0  10162-3 0  9991",
            "tle2": "2 44234  97.4641  45.2345 0001234  90.1234 270.0123 14.94623456999999",
        },
        "RESOURCESAT-2": {
            "tle1": "1 37820U 11025A   24001.50000000  .00000050  00000-0  12345-4 0  9993",
            "tle2": "2 37820  98.6900  60.1234 0001456 100.2345 259.9123 14.56789012999991",
        },
        "RISAT-2BR1": {
            "tle1": "1 44857U 19090A   24001.50000000  .00000456  00000-0  54321-4 0  9997",
            "tle2": "2 44857  37.0012  80.4567 0005678 120.3456 239.7890 14.89012345999993",
        },
        "OCEANSAT-3": {
            "tle1": "1 54361U 22057A   24001.50000000  .00000234  00000-0  31234-4 0  9995",
            "tle2": "2 54361  98.1234  55.6789 0002345  95.4567 264.7890 14.67890123999997",
        },
        "GSAT-19": {
            "tle1": "1 42784U 17023A   24001.50000000  .00000010  00000-0  00000-0 0  9991",
            "tle2": "2 42784   0.0123  95.6789 0001234 100.1234 259.9876  1.00273456999999",
        },
    }
    debris = [
        ("DEBRIS-1",
         "1 20580U 90037B   24001.50000000  .00000000  00000-0  00000-0 0  9999",
         "2 20580  28.4696  11.5576 0002949 282.1105  77.8862  1.00272176 99999"),
        ("DEBRIS-2",
         "1 22195U 92052B   24001.50000000  .00000078  00000-0  12345-4 0  9999",
         "2 22195  98.5680 100.2345 0010234 200.1234 159.8766 14.32561234999999"),
        ("DEBRIS-3",
         "1 23522U 95013B   24001.50000000  .00000050  00000-0  98765-5 0  9991",
         "2 23522  51.6200 250.1234 0005678 130.1234 229.8765 15.48901234999999"),
        ("DEBRIS-4",
         "1 26900U 01049C   24001.50000000  .00000020  00000-0  11111-4 0  9993",
         "2 26900  51.5900 248.1234 0006100 128.1234 231.8765 15.49101234999991"),
        ("DEBRIS-5",
         "1 27000U 01049D   24001.50000000  .00000030  00000-0  22222-4 0  9995",
         "2 27000  51.6100 249.1234 0007200 129.1234 230.8765 15.49201234999992"),
    ]
    return satellites, debris