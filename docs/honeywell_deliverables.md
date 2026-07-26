# Honeywell Challenge: AegisOne Technical Deliverables Report

This document maps the architectural implementation, code pointers, and validation steps of AegisOne to the **7 Honeywell Technical Deliverables**.

---

## 1. Synthetic Data Generator with Injected Attack Taxonomy
* **Component Path**: [backend/app/services/simulation_engine.py](file:///Users/kmrinal/AegisOne/backend/app/services/simulation_engine.py), [backend/app/services/threat_engine/scenarios.py](file:///Users/kmrinal/AegisOne/backend/app/services/threat_engine/scenarios.py)
* **Design & Assumptions**:
  - **Benign Baseline**: Models realistic industrial control system (ICS) operations. Generated users have specific attributes: working shifts, default geolocations, default device models, and browser fingerprints.
  - **Attack Injections**: The threat engine supports 11 scenario templates, including the five Honeywell challenge scenarios:
    - *Impossible Travel*: Authenticates a user from locations thousands of miles apart (e.g. Munich to Houston) within implausible windows.
    - *Device Spoofing*: Interacts with a device while presenting mismatched MAC, OS version, or browser agent details.
    - *Credential Stuffing*: Launches rapid failed logins across multiple target usernames from a single source IP.
    - *Low-and-Slow Exfiltration*: Transfers periodic small chunks of data (e.g., 30 KB database pulls) off-hours to avoid event-volume alerts.
    - *Insider Drift*: Gradually expands command frequencies, shift boundaries, and accessed assets.

---

## 2. Baseline Profiling Model
* **Component Path**: [backend/app/services/detection_engine/training.py](file:///Users/kmrinal/AegisOne/backend/app/services/detection_engine/training.py)
* **Model Implementation**:
  - AegisOne trains a dedicated **Isolation Forest** model (via `scikit-learn`) for each entity type (`User`, `Device`, `IndustrialAsset`, `Department`).
  - **Feature Vector Ingestion**: Vectors are generated dynamically by the Feature Store over rolling 1-hour and 24-hour windows.
  - **Perturbation & Synthesis**: For entities with sparse histories, the engine perturbs baseline peer configurations using Gaussian noise (10% standard deviation) to construct robust decision boundaries and avoid overfitting.

---

## 3. Anomaly Detection Model
* **Component Path**: [backend/app/services/detection_engine/prediction.py](file:///Users/kmrinal/AegisOne/backend/app/services/detection_engine/prediction.py)
* **Inference Pipeline**:
  - The prediction engine executes predictions asynchronously as events trigger.
  - **Cold Start Handling**: If a brand-new entity has fewer than the configured baseline observations, the system calculates peer baseline averages (matching same role or department) and mathematically blends them (weighted by observation counts) to prevent false alerts.
  - **Concept Drift**: Dynamic sensitivity configurations can be adjusted live on the Operations Page.

---

## 4. Anomaly Classification Engine
* **Component Path**: [backend/app/services/detection_engine/prediction.py](file:///Users/kmrinal/AegisOne/backend/app/services/detection_engine/prediction.py) (Lines 237-264), [backend/app/services/detection_engine/advanced_rules.py](file:///Users/kmrinal/AegisOne/backend/app/services/detection_engine/advanced_rules.py)
* **Category Mapping**:
  - AegisOne maps anomalies to specific categories:
    - *Brute Force / Stuffing*: Multi-account failure logs.
    - *Impossible Travel*: Speed velocity exceeds `impossible_travel_threshold` km/h.
    - *Device Spoofing*: Fingerprint mismatch ratio exceeds the sensitivity threshold.
    - *Low-and-Slow Exfiltration*: Sum of byte extractions exceeds threshold limits in the sliding window.
    - *Insider Drift*: High off-shift activity ratio combined with asset/department footprint creep.

---

## 5. Explainability Layer
* **Component Path**: [backend/app/services/copilot/fallback_provider.py](file:///Users/kmrinal/AegisOne/backend/app/services/copilot/fallback_provider.py), [backend/app/services/detection_engine/risk_engine.py](file:///Users/kmrinal/AegisOne/backend/app/services/detection_engine/risk_engine.py)
* **Attribution Details**:
  - Risk calculations combine criticality weights, deviation parameters, and frequency indexes into an explainable score.
  - The AI Security Copilot translates these scores into human-readable briefs:
    - Explains specific trigger attributes (e.g. MAC address changes, speed calculations).
    - Identifies target assets and potential business impact.
    - Suggests actionable remediation checklists for plant operators.

---

## 6. Analyst-Facing SOC Dashboard
* **Component Path**: [frontend/src/pages/DashboardPage.tsx](file:///Users/kmrinal/AegisOne/frontend/src/pages/DashboardPage.tsx), [frontend/src/components/NetworkTopology.tsx](file:///Users/kmrinal/AegisOne/frontend/src/components/NetworkTopology.tsx)
* **Visual Elements**:
  - **Network Topology Map**: An interactive SVG layout mapping DMZ gateway nodes, server racks, engineering workstations, and physical PLCs.
  - **Ranked Alert Queue**: Categorized list of alerts ranked by normalized risk scores (Critical, High, Medium, Low).
  - **Timeline Logs**: Real-time server-sent event (SSE) stream feeds displaying raw protocol events, simulation progression, and threshold modifications.

---

## 7. Assumptions, Metrics & Limitations
- **Key Assumptions**:
  - The local network subnet handles all Modbus, S7Comm, and OPC-UA protocol traffic.
  - Operator working hours baseline represents typical shifts (e.g., 08:00 - 17:00).
- **Core Performance Metrics**:
  - Average API query latencies: **< 15ms**.
  - Local Vite frontend bundle: **~421 KB**.
  - Anomaly scoring inference: **< 5ms** per entity evaluation.
- **Known Limitations**:
  - Requires training data baselines before triggering unsupervised predictions (mitigated by peer-blending fallbacks).
  - Local database file storage requires periodic cleanups during continuous 24/7 logging loops.
