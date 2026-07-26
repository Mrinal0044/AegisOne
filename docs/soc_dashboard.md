# Security Operations Center (SOC) Dashboard Architecture

AegisOne's frontend console is a real-time Security Operations Center (SOC) designed to inspect, trace, and respond to industrial cyber threats.

---

## 1. SOC System Architecture

```
        +----------------------------------------+
        |             React Web UI               |
        +----------------------------------------+
             |                              ^
             | (Rest Control APIs)          | (Server-Sent Events stream)
             v                              |
        +----------------------------------------+
        |            FastAPI Backend             |
        +----------------------------------------+
             |                              ^
             | (DB Queries)                 | (Pub-Sub Push)
             v                              |
        +----------------------------------------+
        |         PostgreSQL Database            |
        +----------------------------------------+
```

---

## 2. Component Hierarchy

The page structure is organized hierarchically inside the single-page application framework:

- **DashboardPage (SOC Homepage View)**
  - **KPI Metrics Cards Row**: Dynamic grid reflecting active device counts, threat runs, average risk indices, and AI models.
  - **NetworkTopology (Digital Twin Model)**: Animated SVG layout connecting target user nodes, host workstations, PLCs, and gateway lines. Nodes change colors based on real-time risk scores.
  - **Incident Injection Form**: Allows operators to fire attack simulation scripts directly from the screen.
  - **Live Alert Queue Table**: Table sorting security alerts. Critical unresolved alerts remain pinned at the top.
    - **AlertInvestigation (Side Drawer Inspector)**: Detailed file overlay detailing entity profiles, audit timelines, and alert status updates.
  - **Live Event Stream Feed**: Chronological logger of all telemetry.

---

## 3. Real-Time Updates via Server-Sent Events (SSE)

Instead of using resource-intensive polling, AegisOne operates an event-driven pub-sub loop via the streaming endpoint `GET /sse/stream`:

1. **Client Event Source**: On dashboard mount, the React client starts a connection:
   `const eventSource = new EventSource('/api/v1/sse/stream')`
2. **Channel Listeners**:
   - `EVENT_CREATED`: Inserts new raw telemetry events directly into the event stream list.
   - `ALERT_CREATED` / `ALERT_UPDATED`: Injects new alerts into the SOC queue, updating KPI numbers.
   - `RISK_UPDATED`: Refreshes specific node risk values inside the network map state.
   - `THREAT_PROGRESS`: Updates the timeline step and scenario progress bar.

---

## 4. SOC Operator Workflow

A security analyst follows a structured investigation loop:
1. **Detection**: An active threat simulation runs, generating anomalous behaviors.
2. **Alert Triaging**: The AI Anomaly Detection Engine raises a high-risk alarm that appears instantly at the top of the Alert Queue.
3. **Investigation**: The analyst clicks the alert row, opening the **SOC Incident File** drawer.
4. **Timeline Mapping**: The timeline panel traces the steps from initial out-of-hours login to Modbus/S7Comm register manipulation.
5. **Mitigation & Resolution**: The analyst assigns the incident, coordinates mitigations, and changes the alert status to `Resolved`.
