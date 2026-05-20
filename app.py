# app.py
# DebrisWatch AI — Main Application
# Monitors ALL Indian ISRO satellites

from flask import Flask, render_template, jsonify
from core.orbital import (
    INDIAN_SATELLITES,
    SAT_COLORS,
    get_sat_position,
    get_debris_approach
)
from core.risk import (
    calculate_score,
    get_risk_label,
    get_action
)
from core.alerts import generate_report
from datetime import datetime
import math
import numpy as np

app = Flask(__name__)


def clean_value(v):
    """
    Convert NumPy / invalid values into
    JSON-safe Python values
    """

    # NumPy integers/floats
    if isinstance(v, (np.integer,)):
        return int(v)

    if isinstance(v, (np.floating,)):
        if math.isnan(v):
            return 0
        return float(v)

    # Python float NaN
    if isinstance(v, float):
        if math.isnan(v):
            return 0
        return v

    # Lists
    if isinstance(v, list):
        return [clean_value(x) for x in v]

    # Dicts
    if isinstance(v, dict):
        return {
            k: clean_value(val)
            for k, val in v.items()
        }

    return v


def analyse_satellite(sat_info, color):
    """
    Full analysis for ONE satellite
    """

    pos, vel, alt = get_sat_position(
        sat_info["tle1"],
        sat_info["tle2"]
    )

    debris_raw = get_debris_approach(pos, vel)

    debris_results = []

    for d in debris_raw:

        score = calculate_score(
            d["min_dist"],
            d["min_hour"],
            d["min_rv"]
        )

        label, rcol = get_risk_label(score)
        action = get_action(score)

        debris_results.append({
            "name": clean_value(d["name"]),
            "score": clean_value(score),
            "label": clean_value(label),
            "risk_color": clean_value(rcol),
            "graph_color": clean_value(
                d["graph_color"]
            ),
            "min_dist": round(
                clean_value(d["min_dist"]), 2
            ),
            "min_hour": clean_value(
                d["min_hour"]
            ),
            "hourly": clean_value(
                d["hourly"]
            ),
            "action": clean_value(action),
        })

    # Prevent empty debris crash
    if not debris_results:
        top_score = 0
        top_label = "SAFE"
        top_c = "#34D399"

    else:
        debris_results.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        top_score = debris_results[0]["score"]
        top_label, top_c = get_risk_label(
            top_score
        )

    return {
        "name": clean_value(
            sat_info["name"]
        ),

        "purpose": clean_value(
            sat_info["purpose"]
        ),

        "altitude": round(
            clean_value(alt), 2
        ),

        "color": clean_value(color),

        "top_score": clean_value(
            top_score
        ),

        "top_label": clean_value(
            top_label
        ),

        "top_color": clean_value(
            top_c
        ),

        "debris": clean_value(
            debris_results
        ),

        "high": sum(
            1 for d in debris_results
            if d["label"] in [
                "CRITICAL",
                "HIGH"
            ]
        ),

        "safe": sum(
            1 for d in debris_results
            if d["label"] in [
                "LOW",
                "MINIMAL"
            ]
        ),
    }


def run_full_analysis():
    """
    Analyse ALL Indian satellites
    """

    satellites = []
    all_debris = []

    for i, sat in enumerate(
        INDIAN_SATELLITES
    ):

        color = SAT_COLORS[
            i % len(SAT_COLORS)
        ]

        result = analyse_satellite(
            sat,
            color
        )

        satellites.append(result)

        all_debris.extend(
            result["debris"]
        )

    # Sort satellites by risk
    satellites.sort(
        key=lambda x: x["top_score"],
        reverse=True
    )

    # Generate alert report
    flat_results = []

    for sat in satellites:

        for d in sat["debris"]:

            flat_results.append({
                **d,
                "sat_name": sat["name"]
            })

    flat_results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # Generate text report
    generate_report(flat_results)

    # History placeholders
    hist_data = {}
    sat_colors = SAT_COLORS[:len(satellites)]

    data = {
        "generated": datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M UTC"
        ),

        "satellites": clean_value(
            satellites
        ),

        "total_sats": len(
            satellites
        ),

        "total_high": sum(
            s["high"] for s in satellites
        ),

        "total_safe": sum(
            s["safe"] for s in satellites
        ),

        # IMPORTANT FIXES
        "hist_data": clean_value(
            hist_data
        ),

        "sat_colors": clean_value(
            sat_colors
        ),

        "total_scans": 0,

        "highest": None,
    }

    return clean_value(data)


@app.route("/")
def index():

    data = run_full_analysis()

    return render_template(
        "dashboard.html",
        data=data
    )


@app.route("/api/data")
def api():

    return jsonify(
        run_full_analysis()
    )


if __name__ == "__main__":

    print("\n" + "=" * 55)

    print("   🛰️ DebrisWatch AI")
    print("   Monitoring Indian Satellites")
    print("   Open: http://127.0.0.1:5000")

    print("=" * 55 + "\n")

    app.run(
        debug=True
    )