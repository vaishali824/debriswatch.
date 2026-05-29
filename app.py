from flask import (
    Flask, render_template,
    jsonify
)
from core.orbital      import (
    SAT_COLORS, SAT_PURPOSES,
    get_sat_position,
    get_debris_approach
)
from core.risk         import (
    calculate_score,
    get_risk_label,
    get_action
)
from core.alerts       import generate_report
from core.database     import (
    init_db, save_scan,
    get_all_history,
    get_total_scans,
    get_highest_ever,
    log_conjunction_event,
    get_conjunction_events,
    get_conjunction_stats
)
from core.ml_model     import (
    predict_collision,
    get_model_stats,
    train_model
)
from core.email_alert  import check_and_alert
from core.tle_fetcher  import get_tle_data
from core.maneuver     import get_maneuver_summary
from datetime import datetime
import numpy as np
import os

app = Flask(__name__)

# Initialize on startup
init_db()
if not os.path.exists("core/debris_model.pkl"):
    train_model()

# Conjunction threshold
# Log event if debris within 5000 km
CONJUNCTION_THRESHOLD = 5000

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
        maneuver = get_maneuver_summary(
            sat_name     = sat_name,
            debris_name  = d["name"],
            ml_prob      = ml["probability"],
            sat_altitude = alt,
            min_dist     = d["min_dist"],
            min_hour     = d["min_hour"],
        )

        # Log conjunction event
        # if debris within threshold
        if d["min_dist"] <= \
                CONJUNCTION_THRESHOLD:
            dv  = 0.0
            fkg = 0.0
            if maneuver["needed"] and \
               maneuver["all_options"]:
                best = maneuver[
                    "all_options"
                ][0]
                dv  = best["delta_v"]
                fkg = best["fuel_kg"]

            log_conjunction_event(
                sat_name    = sat_name,
                debris_name = d["name"],
                distance_km = d["min_dist"],
                tca_hour    = d["min_hour"],
                ml_prob     = ml["probability"],
                risk_level  = ml["label"],
                maneuver_needed = \
                    maneuver["needed"],
                delta_v_ms  = dv,
                fuel_kg     = fkg,
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
            "maneuver":    maneuver,
        })

    debris_results.sort(
        key=lambda x: x["ml_prob"],
        reverse=True
    )

    top_score        = \
        debris_results[0]["score"]
    top_label, top_c = \
        get_risk_label(top_score)
    top_ml_prob = \
        debris_results[0]["ml_prob"]

    top_maneuver = None
    for d in debris_results:
        if d["maneuver"]["needed"]:
            top_maneuver = d["maneuver"]
            break

    return {
        "name":         sat_name,
        "purpose":      purpose,
        "altitude":     alt,
        "color":        color,
        "top_score":    top_score,
        "top_label":    top_label,
        "top_color":    top_c,
        "top_ml_prob":  top_ml_prob,
        "debris":       debris_results,
        "top_maneuver": top_maneuver,
        "high":         sum(
            1 for d in debris_results
            if d["ml_prob"] >= 50
        ),
        "safe":         sum(
            1 for d in debris_results
            if d["ml_prob"] < 30
        ),
    }

def run_full_analysis():
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
        key=lambda x: x["ml_prob"],
        reverse=True
    )
    generate_report(flat)

    print("\n  Checking email alerts...")
    check_and_alert(satellites)

    history     = get_all_history()
    total_scans = get_total_scans()
    highest     = get_highest_ever()

    hist_data = {}
    for sat_name, date, max_score \
            in history:
        if sat_name not in hist_data:
            hist_data[sat_name] = {
                "dates":  [],
                "scores": []
            }
        hist_data[sat_name][
            "dates"
        ].append(date)
        hist_data[sat_name][
            "scores"
        ].append(max_score)

    # Conjunction stats
    conj_stats  = get_conjunction_stats()
    conj_events = get_conjunction_events(
        days=7
    )

    # Format events for template
    events_list = []
    for row in conj_events[:20]:
        (logged_at, sat_name, debris_name,
         dist, tca, prob, level,
         man_needed, dv, fkg) = row
        events_list.append({
            "logged_at":   logged_at,
            "sat_name":    sat_name,
            "debris_name": debris_name,
            "distance_km": round(dist, 1),
            "tca_hour":    tca,
            "ml_prob":     round(prob, 1),
            "risk_level":  level,
            "maneuver":    bool(man_needed),
            "delta_v":     round(dv, 2),
            "fuel_kg":     round(fkg, 2),
        })

    # Format daily chart data
    daily_dates    = []
    daily_counts   = []
    daily_maneuvers = []
    for row in conj_stats["daily"]:
        date, cnt, mans = row
        daily_dates.append(date)
        daily_counts.append(cnt)
        daily_maneuvers.append(
            mans if mans else 0
        )

    return {
        "generated":    datetime.utcnow(
            ).strftime("%Y-%m-%d %H:%M UTC"),
        "satellites":   satellites,
        "total_sats":   len(satellites),
        "total_high":   sum(
            s["high"] for s in satellites
        ),
        "total_safe":   sum(
            s["safe"] for s in satellites
        ),
        "total_scans":  total_scans,
        "highest":      highest,
        "hist_data":    hist_data,
        "sat_colors":   SAT_COLORS,
        "ml_stats":     get_model_stats(),
        "conj_stats":   conj_stats,
        "conj_events":  events_list,
        "daily_dates":  daily_dates,
        "daily_counts": daily_counts,
        "daily_mans":   daily_maneuvers,
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

@app.route("/api/conjunctions")
def conjunctions():
    """
    Dedicated API for conjunction events
    CDM compatible format
    """
    events = get_conjunction_events(days=7)
    result = []
    for row in events:
        (logged_at, sat_name, debris_name,
         dist, tca, prob, level,
         man_needed, dv, fkg) = row
        result.append({
            "MESSAGE_FOR":    sat_name,
            "OBJECT":         debris_name,
            "TCA":            f"T+{tca}h",
            "MISS_DISTANCE":  dist,
            "PROBABILITY":    prob,
            "RISK_LEVEL":     level,
            "CAM_REQUIRED":   bool(man_needed),
            "DELTA_V_MS":     dv,
            "FUEL_KG":        fkg,
            "LOGGED_AT":      logged_at,
        })
    return jsonify({
        "format":  "CDM-compatible",
        "source":  "DebrisWatch AI",
        "events":  result,
        "total":   len(result),
    })

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  DebrisWatch AI")
    print("  Conjunction Event Log Active")
    print("  CDM Compatible API Ready")
    print("  Open: http://127.0.0.1:5000")
    print("="*50 + "\n")
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )