# AegisOne - Live Hackathon Demo Guide & Checklist

This guide provides a step-by-step walkthrough for presenting a live demonstration of AegisOne's capabilities.

---

## Prerequisites & Launch

### 1. Start System Infrastructure
Choose one of the two start methods:
- **Docker Compose (Recommended)**:
  ```bash
  docker compose up -d
  ```
- **Local Host Execution**:
  - Run the database container: `docker compose up -d db`
  - Start the local backend:
    ```bash
    cd backend
    source venv/bin/activate
    POSTGRES_HOST=localhost POSTGRES_PORT=5442 python -m uvicorn app.main:app --port 8002 --reload
    ```
  - Start the local frontend:
    ```bash
    cd frontend
    npm run dev
    ```

### 2. Verify System Health Checks
- Navigate to the **Operations Console**: [http://localhost:5173/operations](http://localhost:5173/operations)
- Confirm CPU, RAM, Disk meters load, and the **System Health Checks** box reports database connections as **Connected**.
- Point out the **Central System Audit Log** feeds displaying startup activities.

---

## Live Threat Simulation Walkthrough

### 3. Navigate to Threat Simulation Center
- Click **Threat Simulation** in the left sidebar navigation.
- Explain: *"Here we can inject realistic OT/ICS cybersecurity attack vectors into our Digital Twin to observe the detection engine in action."*

### 4. Trigger Credential Stuffing Attack
- Click **Run Simulation** next to the **Credential Stuffing Sweep** scenario.
- Explain: *"This scenario simulates a rapid credential stuffing sequence against multiple operator accounts, ending in a compromise."*

---

## Real-Time SOC Dashboard & Investigation

### 5. Monitor the Live Dashboard
- Click **Dashboard** in the sidebar.
- Watch the **Digital Twin Topology Map** update dynamically.
- Explain: *"The topology map animates data links and node status in real time. We can see nodes highlighting in yellow and red as suspicious activities are processed."*

### 6. Inspect the Anomaly Alert
- Once the alarm triggers, click the **Alert Investigation Drawer** (or click the alert card).
- Highlight the **Honeywell-aligned telemetry metrics**:
  - Mismatched MAC Address.
  - Unexpected operating system version mismatch (e.g. Kali Linux instead of Windows baseline).
  - Browser fingerprint signatures mismatch.

---

## AI Copilot & Remediation

### 7. Invoke the AI Security Copilot
- Select the **AI Security Copilot** tab inside the alert drawer.
- Walk the audience through the panels:
  - **AI Explanation**: Understand why the anomaly was raised.
  - **Remediation Guide**: Actions recommended for the OT operator.
  - **Executive Summary**: A brief for the SOC manager.

### 8. Review Audit Logs & Performance
- Click **Operations** to return to the admin panel.
- Review the logged actions under **System Audit logs** verifying that every trigger, configuration change, and alert resolution was chronologically tracked.
- Download the generated logs as a CSV file to show export compliance.
