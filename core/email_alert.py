# email_alert.py
# Sends email alerts when collision
# probability crosses threshold

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ─────────────────────────────────
# YOUR EMAIL SETTINGS
# Replace with your details
# ─────────────────────────────────
SENDER_EMAIL    = "provaishali8@gmail.com"
SENDER_PASSWORD = "huiojshihgdpnhle"
RECEIVER_EMAIL  = "provaishali8@gmail.com"

# Alert threshold
# Send email if ML probability > this value
ALERT_THRESHOLD = 60

def send_alert_email(satellite_name,
                     debris_name,
                     ml_prob,
                     min_dist,
                     min_hour):
    """
    Send email alert for high risk debris
    """
    try:
        # Create email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = (
            f"🚨 DebrisWatch ALERT — "
            f"{satellite_name} at risk!"
        )
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = RECEIVER_EMAIL

        # Email body — plain text
        text = f"""
DEBRISWATCH AI — COLLISION ALERT
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

SATELLITE  : {satellite_name}
DEBRIS     : {debris_name}
ML RISK    : {ml_prob}% collision probability
DISTANCE   : {min_dist} km at closest approach
TIME       : T+{min_hour} hours from now

RECOMMENDED ACTION:
{"MANEUVER IMMEDIATELY" if ml_prob >= 70
 else "PREPARE MANEUVER PLAN"}

This alert was generated automatically
by DebrisWatch AI monitoring system.
        """

        # Email body — HTML version
        html = f"""
<html>
<body style="background:#060810;
             color:#C9D1D9;
             font-family:monospace;
             padding:20px">

  <div style="background:#0D1117;
              border:2px solid #FF4757;
              border-radius:12px;
              padding:24px;
              max-width:600px;
              margin:0 auto">

    <h1 style="color:#FF4757;font-size:20px">
      🚨 DebrisWatch AI — Collision Alert
    </h1>
    <p style="color:#8B949E;font-size:12px">
      {datetime.utcnow().strftime(
          '%Y-%m-%d %H:%M UTC')}
    </p>

    <hr style="border-color:#1C2333;margin:16px 0">

    <table style="width:100%;
                  border-collapse:collapse">
      <tr>
        <td style="color:#8B949E;
                   padding:8px 0;
                   font-size:13px">
          SATELLITE
        </td>
        <td style="color:white;
                   font-weight:bold;
                   font-size:13px">
          {satellite_name}
        </td>
      </tr>
      <tr>
        <td style="color:#8B949E;
                   padding:8px 0;
                   font-size:13px">
          DEBRIS OBJECT
        </td>
        <td style="color:white;
                   font-size:13px">
          {debris_name}
        </td>
      </tr>
      <tr>
        <td style="color:#8B949E;
                   padding:8px 0;
                   font-size:13px">
          ML RISK
        </td>
        <td style="color:#FF4757;
                   font-weight:bold;
                   font-size:20px">
          {ml_prob}% collision probability
        </td>
      </tr>
      <tr>
        <td style="color:#8B949E;
                   padding:8px 0;
                   font-size:13px">
          CLOSEST APPROACH
        </td>
        <td style="color:white;
                   font-size:13px">
          {min_dist} km at T+{min_hour}h
        </td>
      </tr>
    </table>

    <hr style="border-color:#1C2333;
               margin:16px 0">

    <div style="background:#FF475722;
                border:1px solid #FF4757;
                border-radius:8px;
                padding:12px 16px;
                font-size:14px;
                color:#FF4757;
                font-weight:bold">
      {"⚠️ MANEUVER IMMEDIATELY"
       if ml_prob >= 70
       else "🔶 PREPARE MANEUVER PLAN"}
    </div>

    <p style="color:#8B949E;
              font-size:11px;
              margin-top:16px">
      Sent by DebrisWatch AI —
      ISRO Satellite Monitoring System
    </p>
  </div>
</body>
</html>
        """

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html,  "html"))

        # Send email
        with smtplib.SMTP_SSL(
            "smtp.gmail.com", 465
        ) as server:
            server.login(
                SENDER_EMAIL,
                SENDER_PASSWORD
            )
            server.sendmail(
                SENDER_EMAIL,
                RECEIVER_EMAIL,
                msg.as_string()
            )

        print(f"  ✅ Alert email sent for "
              f"{satellite_name} — "
              f"{debris_name} ({ml_prob}%)")
        return True

    except Exception as e:
        print(f"  ❌ Email failed: {e}")
        return False

def check_and_alert(satellites):
    """
    Check all satellites for high risk
    Send email if threshold crossed
    """
    alerts_sent = 0

    for sat in satellites:
        for d in sat["debris"]:
            if d["ml_prob"] >= ALERT_THRESHOLD:
                sent = send_alert_email(
                    satellite_name = sat["name"],
                    debris_name    = d["name"],
                    ml_prob        = d["ml_prob"],
                    min_dist       = d["min_dist"],
                    min_hour       = d["min_hour"],
                )
                if sent:
                    alerts_sent += 1

    if alerts_sent == 0:
        print("  ✅ No alerts needed — "
              "all satellites safe")

    return alerts_sent