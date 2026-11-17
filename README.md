# DebrisWatch AI: 72-Hour Orbital Conjunction Prediction & Risk Scoring Architecture

[![Python](https://shields.io)](https://python.org)
[![Propagator](https://shields.io)](#1-orbital-propagation-methodology)
[![Data Source](https://shields.io)](#2-monitored-orbital-assets)

**Author:** Muddasani Vaishali  
**Affiliation:** Department of Computer Science & Engineering, Mahaveer Institute of Science and Technology, Hyderabad, India  

---

## Abstract

The rapid proliferation of Low Earth Orbit (LEO) and Geostationary (GEO) space debris poses a critical collision hazard to operational national space assets. Standard conjunction screening windows typically alert operators within a 24-hour horizon, leaving narrow margins for propellant-efficient collision avoidance maneuvers. **DebrisWatch AI** is an automated Space Situational Awareness (SSA) and conjunction risk-assessment pipeline designed to extend predictive screening to a **72-hour lookahead window**. Ingesting live Two-Line Element (TLE) sets from the NASA Space-Track catalog, the system propagates state vectors via the **SGP4** perturbation model and evaluates close-approach geometry using a deterministic **100-point multi-factor risk scoring engine**, extending operational decision lead times by $3\times$.

---

## 1. Orbital Propagation Methodology

DebrisWatch AI models orbital trajectories in the True Equator, Mean Equinox (TEME) coordinate frame using the **Simplified General Perturbations 4 (SGP4)** analytical propagator:

1. **Telemetry Ingestion:** Fetches updated Two-Line Element (TLE) sets (mean motion, eccentricity, inclination, right ascension of the ascending node, argument of perigee, and B* drag term) via the Space-Track REST API.
2. **72-Hour State Vector Propagation:** Propagates position $\mathbf{r}(t) \in \mathbb{R}^3$ and velocity $\mathbf{v}(t) \in \mathbb{R}^3$ across discrete time steps $t \in [t_0, t_0 + 72\text{ hours}]$.
3. **Closest Approach Screening:** Computes pairwise Euclidean separation distance $d(t) = \|\mathbf{r}_{\text{sat}}(t) - \mathbf{r}_{\text{deb}}(t)\|_2$ and relative closing velocity $v_{\text{rel}}(t) = \|\mathbf{v}_{\text{sat}}(t) - \mathbf{v}_{\text{deb}}(t)\|_2$ to identify Time of Closest Approach (TCA) events.

---

## 2. Monitored Operational Satellites

The baseline configuration tracks active Indian Space Research Organisation (ISRO) assets across sun-synchronous, low-Earth, and geostationary regimes:

| Satellite Asset | NORAD / Mission Role | Orbital Regime | Strategic Significance |
| :--- | :--- | :--- | :--- |
| **CARTOSAT-3** | High-Resolution Earth Imaging | LEO (SSO) | Sub-meter optical surveillance & cartography |
| **RESOURCESAT-2** | Multispectral Remote Sensing | LEO (SSO) | Agriculture, land-use & water resource mapping |
| **RISAT-2BR1** | X-Band Synthetic Aperture Radar | LEO | All-weather day/night radar imaging |
| **OCEANSAT-3** | Ocean Color & Scatterometer | LEO (SSO) | Marine meteorology & oceanographic monitoring |
| **GSAT-19** | High-Throughput Communications | GEO | Ka/Ku-band national telecommunications |

---

## 3. Deterministic Conjunction Risk Engine (0–100 Scale)

To prioritize actionable conjunction warnings and filter benign orbital passes, DebrisWatch AI evaluates every detected close approach using a weighted multi-factor composite score $R \in [0, 100]$:

$$R = W_{\text{dist}} + W_{\text{time}} + W_{\text{vel}} + W_{\text{orbit}}$$

| Risk Factor | Weight Allocation | Evaluation Metric | Physical & Operational Rationale |
| :--- | :---: | :--- | :--- |
| **Minimum Miss Distance** | **40 pts** | $d_{\min} = \min_{t} \|\mathbf{r}_{\text{sat}}(t) - \mathbf{r}_{\text{deb}}(t)\|_2$ | Primary geometric indicator of physical collision likelihood |
| **Time Urgency (TCA)** | **25 pts** | $\Delta t = t_{\text{TCA}} - t_{\text{now}}$ | Prioritizes imminent encounters requiring immediate maneuver planning |
| **Relative Closing Velocity** | **20 pts** | $v_{\text{rel}} = \|\mathbf{v}_{\text{sat}} - \mathbf{v}_{\text{deb}}\|_2$ | Quantifies hypervelocity kinetic energy transfer ($E_k \propto v_{\text{rel}}^2$) |
| **Orbital Regime Density** | **15 pts** | Altitude / Inclination Shell | Accounts for spatial debris flux density in congested LEO shells |
| **Total Composite Score** | **100 pts** | **Actionable Threat Rank** | Categorizes events into Low, Moderate, High, and Critical alert tiers |

---

## 4. System Architecture & Key Capabilities

* **Extended 72-Hour Horizon:** Provides $3\times$ greater lead time than conventional 24-hour screening windows, supporting early delta-$v$ trajectory optimization.
* **Persistent Telemetry & Audit Logging:** Stores historical TLE snapshots, conjunction geometries, and risk score trajectories in a relational **SQLite** database for longitudinal trend analysis.
* **Automated Alerting & Reporting:** Generates structured conjunction assessment reports automatically when composite risk scores exceed critical thresholds.
* **Interactive Visualization Dashboard:** Real-time **Flask** and **Chart.js** interface displaying live orbital separations, risk distributions, and asset-level health status.

---

## 5. Quick Start & Local Deployment

### Prerequisites
* Python 3.8 or higher
* Active credentials for the [NASA Space-Track API](https://space-track.org)

### Installation & Execution
```bash
git clone https://github.com
cd debriswatch
pip install -r requirements.txt
python app.py
```
Once running, open your browser and navigate to `http://127.0.0.1:5000` to view the live conjunction monitoring dashboard.

---

## 6. Research Relevance & Future Extensions

DebrisWatch AI aligns with space-domain awareness initiatives such as **ISRO Project NETRA** (Network for Space Object Tracking and Analysis). Planned research extensions include:
1. Incorporating covariance matrix error ellipsoids to compute analytical **Probability of Collision ($P_c$)** via Foster/Alfano 2D Gaussian integration.
2. Integrating machine learning residual corrections on top of SGP4 to reduce atmospheric drag propagation errors over multi-day horizons.

---

## Citation

```bibtex
@misc{muddasani_debriswatch_2026,
  title  = {DebrisWatch AI: 72-Hour Orbital Conjunction Prediction and Risk Scoring Architecture},
  author = {Muddasani, Vaishali},
  year   = {2026},
  note   = {Department of Computer Science and Engineering, Mahaveer Institute of Science and Technology}
}
```
