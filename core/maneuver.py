# maneuver.py
# Orbital Maneuver Calculator
# Finds minimum fuel path to avoid collision
# Uses simplified Hohmann transfer equations

import numpy as np

# Earth constants
MU    = 398600.4418  # km³/s² gravitational param
RE    = 6371.0       # km Earth radius
SAFE_DISTANCE = 500  # km minimum safe distance

def calculate_orbital_velocity(altitude_km):
    """
    Calculate orbital velocity at given altitude
    v = sqrt(mu / r)
    """
    r = RE + altitude_km
    return np.sqrt(MU / r)

def calculate_delta_v(
    current_alt, target_alt
):
    """
    Calculate delta-V needed to change orbit
    Uses Hohmann transfer formula

    delta_v = v2 - v1
    """
    v1 = calculate_orbital_velocity(current_alt)
    v2 = calculate_orbital_velocity(target_alt)
    return abs(v2 - v1)

def calculate_fuel_mass(
    delta_v_ms,
    sat_mass_kg=1000,
    isp=220
):
    """
    Calculate fuel needed using
    Tsiolkovsky rocket equation:
    m_fuel = m_sat * (e^(dv/ve) - 1)
    where ve = isp * g0

    delta_v in m/s
    sat_mass in kg (default 1000kg)
    isp = specific impulse (default 220s)
    """
    g0 = 9.81    # m/s²
    ve = isp * g0

    # Convert delta_v from km/s to m/s
    dv_ms = delta_v_ms * 1000

    fuel = sat_mass_kg * (
        np.exp(dv_ms / ve) - 1
    )
    return round(fuel, 2)

def get_maneuver_options(
    sat_altitude,
    min_dist,
    min_hour,
    debris_altitude=None
):
    """
    Calculate 3 maneuver options:
    1. Prograde (raise orbit)
    2. Retrograde (lower orbit)
    3. Radial (sideways)

    Returns best option with details
    """
    # How much altitude change needed
    # to reach safe distance
    alt_change_needed = max(
        SAFE_DISTANCE - min_dist, 50
    ) / 10  # simplified calculation

    options = []

    # ── Option 1: Prograde ──────────────
    prograde_dv = calculate_delta_v(
        sat_altitude,
        sat_altitude + alt_change_needed
    )
    prograde_fuel = calculate_fuel_mass(
        prograde_dv
    )
    options.append({
        "type":        "PROGRADE",
        "description": "Speed up — raise orbit",
        "delta_v":     round(prograde_dv * 1000, 2),
        "fuel_kg":     prograde_fuel,
        "new_alt":     round(
            sat_altitude + alt_change_needed, 1
        ),
        "execute_at":  f"T+{max(min_hour-6, 1)}h",
        "safe_dist":   round(
            min_dist + alt_change_needed * 10, 1
        ),
        "recommended": True,
    })

    # ── Option 2: Retrograde ────────────
    retro_dv   = calculate_delta_v(
        sat_altitude,
        sat_altitude - alt_change_needed
    )
    retro_fuel = calculate_fuel_mass(retro_dv)
    options.append({
        "type":        "RETROGRADE",
        "description": "Slow down — lower orbit",
        "delta_v":     round(retro_dv * 1000, 2),
        "fuel_kg":     retro_fuel,
        "new_alt":     round(
            sat_altitude - alt_change_needed, 1
        ),
        "execute_at":  f"T+{max(min_hour-6, 1)}h",
        "safe_dist":   round(
            min_dist + alt_change_needed * 8, 1
        ),
        "recommended": False,
    })

    # ── Option 3: Radial ────────────────
    radial_dv   = prograde_dv * 1.4
    radial_fuel = calculate_fuel_mass(radial_dv)
    options.append({
        "type":        "RADIAL",
        "description": "Sideways push — last resort",
        "delta_v":     round(radial_dv * 1000, 2),
        "fuel_kg":     radial_fuel,
        "new_alt":     sat_altitude,
        "execute_at":  f"T+{max(min_hour-3, 1)}h",
        "safe_dist":   round(
            min_dist + alt_change_needed * 6, 1
        ),
        "recommended": False,
    })

    # Sort by fuel cost
    options.sort(key=lambda x: x["fuel_kg"])
    options[0]["recommended"] = True

    return options

def get_maneuver_summary(
    sat_name,
    debris_name,
    ml_prob,
    sat_altitude,
    min_dist,
    min_hour
):
    """
    Complete maneuver recommendation
    for one satellite-debris pair
    """
    if ml_prob < 30:
        return {
            "needed":  False,
            "message": "No maneuver needed",
            "options": []
        }

    options = get_maneuver_options(
        sat_altitude, min_dist, min_hour
    )
    best    = options[0]

    urgency = "IMMEDIATE" \
        if ml_prob >= 70 \
        else "PLAN NOW" \
        if ml_prob >= 50 \
        else "MONITOR"

    return {
        "needed":      True,
        "sat_name":    sat_name,
        "debris_name": debris_name,
        "ml_prob":     ml_prob,
        "urgency":     urgency,
        "best_option": best,
        "all_options": options,
        "window":      f"Execute before T+{max(min_hour-6, 1)}h",
        "message":     (
            f"Burn {best['delta_v']} m/s "
            f"{best['type']} at "
            f"{best['execute_at']} — "
            f"costs {best['fuel_kg']} kg fuel"
        )
    }