# risk.py
# Risk Score Engine
# Calculates threat level for each debris object

import numpy as np

def calculate_score(min_dist, min_hour, rel_vel):
    """
    Calculate risk score out of 100
    4 factors: distance, urgency, velocity, orbit
    """
    # Distance score (40 pts)
    if min_dist < 100:    ds = 40
    elif min_dist < 500:  ds = 35
    elif min_dist < 1000: ds = 28
    elif min_dist < 3000: ds = 18
    elif min_dist < 5000: ds = 10
    elif min_dist < 8000: ds = 5
    else:                 ds = 2

    # Time urgency (25 pts)
    if min_hour < 6:      ts = 25
    elif min_hour < 12:   ts = 20
    elif min_hour < 24:   ts = 15
    elif min_hour < 48:   ts = 8
    else:                 ts = 3

    # Relative velocity (20 pts)
    spd = np.sqrt(sum(v**2 for v in rel_vel))
    if spd > 14:   vs = 20
    elif spd > 10: vs = 15
    elif spd > 7:  vs = 10
    elif spd > 3:  vs = 6
    else:          vs = 2

    # Orbit proximity (15 pts)
    if min_dist < 1000:   os = 15
    elif min_dist < 3000: os = 10
    elif min_dist < 6000: os = 5
    else:                 os = 1

    return min(ds + ts + vs + os, 100)

def get_risk_label(score):
    """
    Convert score to human readable label
    """
    if score >= 80:   return "CRITICAL", "#FF4757"
    elif score >= 60: return "HIGH",     "#FF6B35"
    elif score >= 40: return "MEDIUM",   "#F59E0B"
    elif score >= 20: return "LOW",      "#34D399"
    else:             return "MINIMAL",  "#00FFB2"

def get_action(score):
    """
    Recommended action based on score
    """
    if score >= 80:   return "⚠️ MANEUVER NOW"
    elif score >= 60: return "PREPARE MANEUVER"
    elif score >= 40: return "MONITOR CLOSELY"
    else:             return "ROUTINE WATCH"