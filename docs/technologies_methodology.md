# AegisOne: Technologies & Implementation Methodology

This document outlines the software stack, data workflows, and architectural processes powering AegisOne.

---

## 1. Technologies Used

AegisOne leverages a modern, decoupled tech stack optimized for low-latency streaming and high-fidelity anomaly detection:

### Backend Architecture
- **Programming Language**: `Python 3.11+`
- **Application Framework**: `FastAPI` (provides asynchronous request handling, high concurrency, and automatic OpenAPI schema validation).
- **ASGI Web Server**: `Uvicorn` (monitored and managed locally or in container runtimes).
- **ORM / Database Adapter**: `SQLAlchemy 2.0` (with connection pooling) & `psycopg2-binary` (PostgreSQL driver).
- **Database Migrations**: `Alembic` (handles database versioning and schema updates).

### Analytics & Machine Learning
- **Anomaly Detection**: `Scikit-Learn` (Isolation Forest wrapper).
- **Numeric Vector Operations**: `NumPy` & `SciPy` (mathematical vector aggregation and Haversine geodetic distance calculations).

### Frontend Console
- **Framework & Libraries**: `React 19` & `TypeScript` (ensures type safety across pages).
- **Build Tool / Bundler**: `Vite` (fully optimized production assets bundle in under 1 second).
- **Styling Utility**: `Tailwind CSS v4` & `Vanilla CSS` (dark-theme glassmorphism and clean animations).
- **Vector Icons**: `Lucide React`.

### Data Layer & Hosting
- **Relational Database**: `PostgreSQL` (Neon Serverless PostgreSQL in production).
- **Real-Time Data Push**: `Server-Sent Events (SSE)` (provides unidirectional HTTP streaming for active alerts, network topology status, and terminal timeline logs).
- **Cloud Infrastructure**: `Render` (Backend Uvicorn Service) & `Vercel` (Frontend static CDN hosting).

---

## 2. Implementation Methodology & Process

The core behavioral intelligence loop operates on continuous event streams rather than static snapshots. Below are the implementation process flowcharts:

### System Data Flow Architecture

```mermaid
graph TD
    A[Digital Twin Event Stream / Threat Simulation] -->|1. Live Events Ingest| B[FastAPI /events Endpoint]
    B -->|2. Async Event Queue| C[Behavioral Intelligence Pipeline]
    C -->|3. Feature Store Rollup| D[Feature Store Database]
    D -->|4. Active 1h Feature Vector| E[Anomaly Detection Engine]
    E -->|5. ML Inference: Isolation Forest| F[Score & Criticality Fusion]
    F -->|6. Normalized Risk Score 0-100| G[Risk & Alerts Generator]
    G -->|7. SSE Push| H[SOC Dashboard Panel UI]
    G -->|8. Context Payload| I[AI Security Copilot Drawer]
```

### Anomaly Prediction & Cold Start Logic

```mermaid
flowchart TD
    A[Ingest Entity Feature Vector] --> B{Observation Count > Threshold?}
    B -- Yes --> C[Standard Inference Loop]
    B -- No --> D[Peer Category Lookup]
    D --> E[Retrieve Peer Role/Type Vectors]
    E --> F[Calculate Average Peer Vector]
    F --> G[Blend Vectors: weight = count / threshold]
    G --> C
    C --> H[Run Isolation Forest Predict]
    H --> I[Assess Advanced Rules checks]
    I --> J[Evaluate Risk Score & Criticality]
```

### Threat Simulation Engine Lifecycle

```mermaid
sequenceDiagram
    participant Analyst
    participant ThreatEngine
    participant Database
    participant BehaviorPipeline
    participant SOCDashboard

    Analyst->>ThreatEngine: Click "Run Simulation" (e.g. Credential Stuffing)
    ThreatEngine->>ThreatEngine: Resolve Target IPs, MACs, & Users
    Loop Over Scenario Steps
        ThreatEngine->>Database: Commit Event (Failed/Successful logins)
        ThreatEngine->>BehaviorPipeline: Push Event ID to Queue
        BehaviorPipeline->>SOCDashboard: Stream Event details via SSE
        Note over BehaviorPipeline: Perform advanced checks & ML inference
        BehaviorPipeline->>SOCDashboard: Stream Alert triggered via SSE
    End
```
