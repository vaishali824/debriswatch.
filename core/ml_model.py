# ml_model.py
# Machine Learning Risk Model
# Trains on historical conjunction data
# Predicts collision probability %

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
import joblib
import os

MODEL_FILE  = "core/debris_model.pkl"
SCALER_FILE = "core/debris_scaler.pkl"

def generate_training_data(n=1000):
    """
    Generate realistic training data
    based on known orbital mechanics patterns

    In real project → replace with actual
    NASA CDM historical data

    Features:
    - min_distance   (km)
    - relative_speed (km/s)
    - time_to_tca    (hours)
    - orbit_alt_diff (km difference in altitude)
    - debris_size    (estimated, 1-10 scale)

    Label:
    - 1 = High risk (needs maneuver)
    - 0 = Low risk  (safe to ignore)
    """
    np.random.seed(42)
    data = []

    for _ in range(n):
        # Generate realistic scenarios
        scenario = np.random.choice(
            ["safe", "risky", "critical"],
            p=[0.6, 0.3, 0.1]
        )

        if scenario == "safe":
            min_dist    = np.random.uniform(500, 5000)
            rel_speed   = np.random.uniform(0.5, 3.0)
            time_to_tca = np.random.uniform(24, 72)
            alt_diff    = np.random.uniform(50, 500)
            debris_size = np.random.uniform(1, 4)
            label       = 0

        elif scenario == "risky":
            min_dist    = np.random.uniform(100, 500)
            rel_speed   = np.random.uniform(2.0, 8.0)
            time_to_tca = np.random.uniform(6, 24)
            alt_diff    = np.random.uniform(5, 50)
            debris_size = np.random.uniform(3, 7)
            label       = np.random.choice([0, 1],
                          p=[0.4, 0.6])

        else:  # critical
            min_dist    = np.random.uniform(1, 100)
            rel_speed   = np.random.uniform(5.0, 15.0)
            time_to_tca = np.random.uniform(1, 12)
            alt_diff    = np.random.uniform(0, 10)
            debris_size = np.random.uniform(5, 10)
            label       = 1

        data.append([
            min_dist, rel_speed, time_to_tca,
            alt_diff, debris_size, label
        ])

    df = pd.DataFrame(data, columns=[
        "min_dist", "rel_speed", "time_to_tca",
        "alt_diff", "debris_size", "label"
    ])
    return df

def train_model():
    """
    Train Random Forest model
    Save to file for reuse
    """
    print("  Training ML model...")

    # Generate training data
    df = generate_training_data(2000)

    # Features and labels
    X = df[[
        "min_dist", "rel_speed",
        "time_to_tca", "alt_diff",
        "debris_size"
    ]].values
    y = df["label"].values

    # Split into train and test
    X_train, X_test, y_train, y_test = \
        train_test_split(
            X, y,
            test_size=0.2,
            random_state=42
        )

    # Scale features
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    # Train Random Forest
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Check accuracy
    y_pred   = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"  ✅ Model trained!")
    print(f"  Accuracy: {accuracy*100:.1f}%")

    # Save model and scaler
    joblib.dump(model,  MODEL_FILE)
    joblib.dump(scaler, SCALER_FILE)
    print(f"  Saved → {MODEL_FILE}")

    return model, scaler, accuracy

def load_model():
    """
    Load saved model
    Train new one if not exists
    """
    if os.path.exists(MODEL_FILE) and \
       os.path.exists(SCALER_FILE):
        model  = joblib.load(MODEL_FILE)
        scaler = joblib.load(SCALER_FILE)
        return model, scaler
    else:
        model, scaler, _ = train_model()
        return model, scaler

def predict_collision(
    min_dist, rel_speed,
    time_to_tca, alt_diff=50,
    debris_size=5
):
    """
    Predict collision probability
    for a single debris object

    Returns:
    - probability % (0-100)
    - risk label
    - color
    """
    model, scaler = load_model()

    # Prepare input
    X = np.array([[
        min_dist, rel_speed,
        time_to_tca, alt_diff,
        debris_size
    ]])
    X_scaled = scaler.transform(X)

    # Get probability
    prob     = model.predict_proba(X_scaled)[0]
    # prob[1] = probability of HIGH RISK
    risk_pct = round(prob[1] * 100, 1)

    # Label based on probability
    if risk_pct >= 70:
        label = "CRITICAL"
        color = "#FF4757"
    elif risk_pct >= 50:
        label = "HIGH"
        color = "#FF6B35"
    elif risk_pct >= 30:
        label = "MEDIUM"
        color = "#F59E0B"
    elif risk_pct >= 15:
        label = "LOW"
        color = "#34D399"
    else:
        label = "MINIMAL"
        color = "#00FFB2"

    return {
        "probability": risk_pct,
        "label":       label,
        "color":       color
    }

def get_model_stats():
    """
    Return model information
    for dashboard display
    """
    if not os.path.exists(MODEL_FILE):
        train_model()

    model, scaler = load_model()

    return {
        "type":       "Random Forest",
        "estimators": 100,
        "features":   [
            "Min Distance",
            "Relative Speed",
            "Time to TCA",
            "Altitude Diff",
            "Debris Size"
        ],
        "trained": True
    }