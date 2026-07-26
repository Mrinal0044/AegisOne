# Behavioral Intelligence AI Detection & Risk Engine Architecture

This document describes the design and components of AegisOne's Behavioral Intelligence Detection Engine, detailing how modular unsupervised models fit normal baselines, evaluate real-time feature streams, normalize risks, and raise alerts.

---

## 1. Abstract Model Architecture

To ensure the platform remains decoupled from any specific algorithm, AegisOne implements a strict modular design pattern.

```
       +-----------------------+
       |   DetectionModel      | (Abstract Interface)
       +-----------------------+
         - train(data)
         - predict(vector)
         - save(path)
         - load(path)
         - get_model_info()
                   ^
                   | (Implements)
       +-----------------------+
       |  IsolationForestModel | (scikit-learn wrapper)
       +-----------------------+
```

### Future Replaceability
If the security center decides to migrate from Isolation Forest to an **Autoencoder** (PyTorch) or **One-Class SVM** (scikit-learn) in the future:
1. Write a new wrapper class inheriting from `DetectionModel` (e.g. `AutoencoderModel`).
2. Implement the interface methods, mapping model inputs/outputs accordingly.
3. Register the new class inside `model_manager.py` without changing a single line of business logic in the training pipeline, prediction engine, or REST APIs.

---

## 2. Training Pipeline

Models are trained on **normal behavior** baselines in the database to establish healthy operational envelopes:

1. **Feature Query**: The training worker pulls historical feature vectors (scoped to the `1h` window) for each entity (User, Device, Asset, Department).
2. **Perturbation (Sparse Data Protection)**: If the system has just started and fewer than 30 baseline vectors are registered, the pipeline automatically synthesizes 50 variations centered around the baseline by adding small Gaussian fluctuations:
   $$\text{Sample} = \text{Baseline} \times (1.0 + \mathcal{N}(0, 0.08))$$
   This prevents scikit-learn from throwing shape errors on singular data points and forms a robust baseline boundary.
3. **Isolation Forest Fitting**: Fits the `IsolationForest` estimator with a default contamination rate of 5%.
4. **Serialization**: Saves the model binary using pickle to `/app/model_store/{entity_type}_{entity_id}.pkl` and records metadata inside `manifest.json`.

---

## 3. Real-Time Prediction & Risk Scoring Pipeline

When the `BehaviorPipeline` processes an event and updates features, it triggers the prediction evaluation:

```
[ New Event Commits ]
        |
        v
[ Aggregators Update Features ]
        |
        v
[ PredictionEngine.evaluate_entity() ]
        |
        +---> 1. Fetch current 1h feature vector
        +---> 2. Load model from ModelManager
        +---> 3. Run model.predict(vector) ---> returns Anomaly Score & prediction (-1 / 1)
        |
        v
[ RiskEngine.calculate_normalized_risk() ]
        |
        v
[ Normalized Risk Score (0-100) ]
        |
        +---> Log to database (`RiskScore` history)
        +---> If Risk Score > 60: Fire Alert via AlertGenerator (with de-duplication)
```

---

## 4. Normalized Risk Engine (0-100)

Raw contamination scores from Isolation Forest do not map cleanly to human operations. The **Risk Engine** combines mathematical anomaly scores, activity frequencies, and physical criticality metrics:

$$\text{Risk Score} = \text{Clamp}\Big(0.4 \times (\text{Anomaly Score} \times 100) + 0.3 \times (\text{Criticality} \times 100) + 0.2 \times (\text{Deviation} \times 100) + 0.1 \times (\text{Frequency} \times 100)\Big)$$

### Risk Factors Matrix
1. **Anomaly Score (40%)**: Distance from the Isolation Forest baseline envelope boundary.
2. **Criticality Weight (30%)**:
   - `Critical (1.0)`: ICS / PLC workstations, Siemens/Modicon PLCs, ICS Operations.
   - `High (0.8)`: Operator stations, Plant Managers.
   - `Medium (0.5)`: Logistics, Maintenance technicians.
   - `Low (0.2)`: Administrative, Finance analysts.
3. **Deviation Weight (20%)**: Night operations ratio, weekend actions ratio, or unexpected downtime.
4. **Frequency Weight (10%)**: Command write frequency density compared to normal baseline.

### Severity Boundaries
- **0–30 (Low)**: Normal actions fitting within baseline thresholds.
- **31–60 (Medium)**: Slight fluctuations or non-critical anomalies.
- **61–80 (High)**: Clear anomaly in critical zones. Triggers warning alert.
- **81–100 (Critical)**: Serious anomaly targeting critical PLCs/workstations. Triggers critical alert.

---

## 5. SOC Alert De-duplication

To prevent **alert fatigue** (a common failure in raw log alert processors), the `AlertGenerator` implements a de-duplication check:
- If a high/critical risk is identified, the generator queries the database for any unresolved alert (`New` or `Investigating`) mapped to the same entity.
- If one exists, it **does not** create a new alert. Instead, it updates the existing description and escalates severity if the new risk score is higher.
- A new alert is generated only if previous alerts for the entity have been resolved or marked as a false positive.
