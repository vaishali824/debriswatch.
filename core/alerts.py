# core/alerts.py
# DebrisWatch AI — Alert Report Generator

from datetime import datetime, UTC
import sys

# Fix Windows Unicode terminal issue
sys.stdout.reconfigure(encoding="utf-8")


def generate_report(results):
    """
    Generate debris threat report
    """

    # Safe fallback
    if not results:
        results = []

    now = datetime.now(UTC)

    # Risk groups
    critical = [
        r for r in results
        if r.get("label") in ["CRITICAL", "HIGH"]
    ]

    medium = [
        r for r in results
        if r.get("label") == "MEDIUM"
    ]

    safe = [
        r for r in results
        if r.get("label") in ["LOW", "MINIMAL"]
    ]

    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("        🛰️ DEBRISWATCH AI — ALERT REPORT")
    lines.append(
        f"        Generated: "
        f"{now.strftime('%Y-%m-%d %H:%M UTC')}"
    )
    lines.append("=" * 60)

    # Summary
    lines.append("")
    lines.append(
        f"  🔴 CRITICAL / HIGH : {len(critical)}"
    )

    lines.append(
        f"  🟠 MEDIUM          : {len(medium)}"
    )

    lines.append(
        f"  🟢 SAFE            : {len(safe)}"
    )

    lines.append("")
    lines.append("  TOP THREATS")
    lines.append("-" * 60)

    # Top threats
    top_results = results[:3]

    if not top_results:

        lines.append("")
        lines.append("  No debris threats found.")

    else:

        for r in top_results:

            lines.append("")

            lines.append(
                f"  🛰️ Satellite : "
                f"{r.get('sat_name', 'Unknown')}"
            )

            lines.append(
                f"  ☄️ Debris    : "
                f"{r.get('name', 'Unknown')}"
            )

            lines.append(
                f"  📊 Score     : "
                f"{r.get('score', 0)}/100"
            )

            lines.append(
                f"  ⚠️ Level     : "
                f"{r.get('label', 'N/A')}"
            )

            lines.append(
                f"  📏 Distance  : "
                f"{r.get('min_dist', 0)} km"
            )

            lines.append(
                f"  ⏱️ Time      : "
                f"T+{r.get('min_hour', 0)}h"
            )

            lines.append(
                f"  🚨 Action    : "
                f"{r.get('action', 'Monitor')}"
            )

            lines.append("-" * 60)

    # Footer
    lines.append("")
    lines.append("=" * 60)

    report = "\n".join(lines)

    # Save safely using UTF-8
    with open(
        "alert_report.txt",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(report)

    # Safe console print
    try:
        print(report)

    except UnicodeEncodeError:
        print(
            report.encode(
                "ascii",
                errors="ignore"
            ).decode()
        )

    return report