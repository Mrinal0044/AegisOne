# Threat Scenario Engine Architecture

The AegisOne **Threat Scenario Engine** allows security operators to run simulated cyberattacks against the industrial plant digital twin, testing pipeline integrations, feature aggregations, and detection parameters in real time.

---

## 1. System Integration Flow

The Threat Scenario Engine sits at the top of the AegisOne data flow, injecting events natively into the industrial event pipeline.

```
       +-------------------------+
       |  Threat Scenario Engine | (Operator triggers Insider, USB, PLC attack)
       +-------------------------+
                    |
                    | 1. Resolves target IPs & Hostnames
                    | 2. Inserts sequential Event records
                    v
       +-------------------------+
       |   Events DB Table       | (PostgreSQL logs store)
       +-------------------------+
                    |
                    | 3. Enqueues Event ID (FIFO)
                    v
       +-------------------------+
       |  BehaviorPipeline Queue | (FastAPI Background worker)
       +-------------------------+
                    |
                    | 4. Incremental Feature Updates
                    v
       +-------------------------+
       |  Postgres Feature Store | (Rolling user/device vectors)
       +-------------------------+
                    |
                    | 5. Inference Prediction & Risk Normalization
                    v
       +-------------------------+
       |  AI Detection Engine    | (Unsupervised Isolation Forest)
       +-------------------------+
                    |
                    | 6. Generates Security Alerts (High/Critical)
                    v
       +-------------------------+
       |   Alerts DB Table       | (SOC Queue display)
       +-------------------------+
                    |
                    | 7. Polled by Threat Engine Status Check
                    v
       +-------------------------+
       | Threat Dashboard (GUI)  | (Displays status: "FLAGGED DETECTED")
       +-------------------------+
```

---

## 2. Supported Scenarios Catalog

AegisOne implements 7 independent industrial attack scripts:
1. **Insider Threat**: Active user session initiated outside shift hours, accessing foreign networks, downloading logical assets, and attempting PLC edits.
2. **Brute Force Login**: Injects a rapid burst of failed authentication audits, followed by a successful login compromise and privilege escalation query.
3. **USB Malware**: Simulates a USB plug-in, unsigned executable launch, configuration logic backup copy, and direct PLC command writes.
4. **PLC Manipulation**: Initiates direct Modbus/TCP session to field PLCs and writes rapid register overrides, bypassing engineering consoles.
5. **Lateral Movement**: Pivot from compromised office environment, initiating remote RDP to engineering stations, launching SCADA software, and querying SQL credentials.
6. **Remote Access**: Simulates connection from a TOR/VPN node (NL IP address) at an abnormal timeframe, scanning PLCs.
7. **Data Exfiltration**: Connects to Historian DB database, dumps archived sensor registries, compresses files, and posts data to external dropzone server.

---

## 3. Timeline Engine & Scenarios Lifecycle

### Scenarios Lifecycle
Simulations execute asynchronously inside independent worker tasks (`asyncio.create_task` managed by the singleton `ThreatEngine` service). Their status transitions:
- `IDLE`: Not started.
- `RUNNING`: Actively injecting step-by-step events at configurable intervals.
- `STOPPED`: Manually cancelled by the operator.
- `COMPLETED`: Run successfully finished.

### Dynamic Target Resolvers
To maintain absolute database consistency, each scenario class implements a target resolver. If the operator selects a target user, host, or asset, the simulation binds to those specific records. If left empty, the engine dynamically queries active database records and resolves target IPs and hostnames on demand.

### Anomaly Flag Detection
When status is queried, the Threat Engine checks for active Alerts raised against the target entity within the attack window. If an alert exists, it flags the simulation status as **Detected** in the GUI console.

---

## 4. Scenario Extension Guide

To add a new attack scenario to AegisOne:

1. **Create Scenario Class**: Implement a new class in `backend/app/services/threat_engine/scenarios.py` inheriting from the abstract `ThreatScenario` base class:
   ```python
   class NewAttackScenario(ThreatScenario):
       @property
       def scenario_id(self) -> str:
           return "new_attack"

       @property
       def name(self) -> str:
           return "New Custom Attack Script"

       @property
       def description(self) -> str:
           return "Description of the attack steps."

       def get_steps(self, db, target_user_id, target_device_id, target_asset_id):
           # Define steps list
           return [...]
   ```
2. **Register Scenario**: Register the scenario inside `backend/app/services/threat_engine/scenario_registry.py` under `_register_default_scenarios()`:
   ```python
   self.register(NewAttackScenario())
   ```
3. The new scenario will automatically load into the React GUI scenarios console and be ready to run via the REST controller.
