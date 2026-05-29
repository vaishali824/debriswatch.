from flask import Flask, render_template, jsonify
from core.orbital    import (
    SAT_COLORS, SAT_PURPOSES,
    get_sat_position, get_debris_approach
)
from core.risk       import (
    calculate_score, get_risk_label, get_action
)
from core.alerts     import generate_report
from core.database   import (
    init_db, save_scan,
    get_all_history, get_total_scans,
    get_highest_ever
)
from core.ml_model   import (
    predict_collision,
    get_model_stats,
    train_model
)
from core.email_alert  import check_and_alert
from core.tle_fetcher  import get_tle_data
from datetime import datetime
import numpy as np
import os

app = Flask(__name__)

# Initialize on startup
init_db()
if not os.path.exists("core/debris_model.pkl"):
    train_model()

def analyse_satellite(
    sat_name, sat_tle, color, debris_list
):
    pos, vel, alt = get_sat_position(
        sat_tle["tle1"], sat_tle["tle2"]
    )
    debris_raw = get_debris_approach(
        pos, vel, debris_list
    )
    purpose = SAT_PURPOSES.get(
        sat_name, "ISRO Satellite"
    )

    debris_results = []
    for d in debris_raw:
        score       = calculate_score(
            d["min_dist"],
            d["min_hour"],
            d["min_rv"]
        )
        label, rcol = get_risk_label(score)
        action      = get_action(score)
        rel_speed   = np.sqrt(sum(
            v**2 for v in d["min_rv"]
        ))
        ml = predict_collision(
            min_dist    = d["min_dist"],
            rel_speed   = rel_speed,
            time_to_tca = d["min_hour"],
        )
        debris_results.append({
            "name":        d["name"],
            "score":       score,
            "label":       label,
            "risk_color":  rcol,
            "graph_color": d["graph_color"],
            "min_dist":    d["min_dist"],
            "min_hour":    d["min_hour"],
            "hourly":      d["hourly"],
            "action":      action,
            "ml_prob":     ml["probability"],
            "ml_label":    ml["label"],
            "ml_color":    ml["color"],
        })

    debris_results.sort(
        key=lambda x: x["ml_prob"], reverse=True
    )

    top_score        = debris_results[0]["score"]
    top_label, top_c = get_risk_label(top_score)
    top_ml_prob = debris_results[0]["ml_prob"]

    return {
        "name":        sat_name,
        "purpose":     purpose,
        "altitude":    alt,
        "color":       color,
        "top_score":   top_score,
        "top_label":   top_label,
        "top_color":   top_c,
        "top_ml_prob": top_ml_prob,
        "debris":      debris_results,
        "high":        sum(
            1 for d in debris_results
            if d["ml_prob"] >= 50
        ),
        "safe":        sum(
            1 for d in debris_results
            if d["ml_prob"] < 30
        ),
    }

def run_full_analysis():
    # Get fresh TLE data
    print("\n  Fetching TLE data...")
    sat_tles, debris_list = get_tle_data()

    satellites = []
    for i, (sat_name, sat_tle) in \
            enumerate(sat_tles.items()):
        color  = SAT_COLORS[
            i % len(SAT_COLORS)
        ]
        result = analyse_satellite(
            sat_name, sat_tle,
            color, debris_list
        )
        satellites.append(result)

    satellites.sort(
        key=lambda x: x["top_ml_prob"],
        reverse=True
    )

    save_scan(satellites)

    flat = []
    for sat in satellites:
        for d in sat["debris"]:
            flat.append({
                **d,
                "sat_name": sat["name"]
            })
    flat.sort(
        key=lambda x: x["ml_prob"], reverse=True
    )
    generate_report(flat)

    print("\n  Checking email alerts...")
    check_and_alert(satellites)

    history     = get_all_history()
    total_scans = get_total_scans()
    highest     = get_highest_ever()

    hist_data = {}
    for sat_name, date, max_score in history:
        if sat_name not in hist_data:
            hist_data[sat_name] = {
                "dates":  [],
                "scores": []
            }
        hist_data[sat_name]["dates"].append(date)
        hist_data[sat_name]["scores"].append(
            max_score
        )

    return {
        "generated":   datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M UTC"),
        "satellites":  satellites,
        "total_sats":  len(satellites),
        "total_high":  sum(
            s["high"] for s in satellites
        ),
        "total_safe":  sum(
            s["safe"] for s in satellites
        ),
        "total_scans": total_scans,
        "highest":     highest,
        "hist_data":   hist_data,
        "sat_colors":  SAT_COLORS,
        "ml_stats":    get_model_stats(),
    }

@app.route("/")
def index():
    data = run_full_analysis()
    return render_template(
        "dashboard.html", data=data
    )

@app.route("/api/data")
def api():
    return jsonify(run_full_analysis())

@app.route("/api/ping")
def ping():
    return jsonify({
        "status": "ok",
        "time":   datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M UTC"
        )
    })

if __name__ == "__main__":
    import os
    print("\n" + "="*50)
    print("  DebrisWatch AI — Feature A")
    print("  Real TLE Auto Download Active")
    print("  Open: http://127.0.0.1:5000")
    print("="*50 + "\n")
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )